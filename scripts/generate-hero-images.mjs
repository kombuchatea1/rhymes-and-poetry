#!/usr/bin/env node
// scripts/generate-hero-images.mjs
//
// Generates hero images for blog posts using Replicate Flux 1.1 Pro.
//
// Reads REPLICATE_API_TOKEN from .env at project root (gitignored).
// Reads prompts from scripts/hero-image-manifest.json.
// Saves images to public/images/blog/{slug}.jpg.
// Updates each post's frontmatter to add a heroImage path.
//
// Usage:
//   node scripts/generate-hero-images.mjs              # generate all missing
//   node scripts/generate-hero-images.mjs --dry-run    # log plan, no API calls
//   node scripts/generate-hero-images.mjs --only namaste,frozen-in-time
//   node scripts/generate-hero-images.mjs --force      # regenerate even if heroImage exists
//   node scripts/generate-hero-images.mjs --skip-mask  # skip the python tear-mask step
//
// After each successful image, the script invokes
//   python3 scripts/generate-tear-mask.py <slug>
// so the per-post torn-paper mask is always in sync with the hero image.
// (Requires Python 3 + Pillow + numpy locally.)

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = join(__dirname, '..');

// --- env loading (lightweight, no dotenv dep) ---
function loadEnv(path) {
  if (!existsSync(path)) return {};
  const out = {};
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    out[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
  }
  return out;
}

const env = { ...loadEnv(join(ROOT, '.env')), ...process.env };
const TOKEN = env.REPLICATE_API_TOKEN;
if (!TOKEN) {
  console.error('Missing REPLICATE_API_TOKEN in .env');
  process.exit(1);
}

// --- args ---
const argv = process.argv.slice(2);
const flags = new Set(argv.filter((a) => a.startsWith('--')));
const DRY_RUN = flags.has('--dry-run');
const FORCE = flags.has('--force');
const SKIP_MASK = flags.has('--skip-mask');
const onlyIdx = argv.indexOf('--only');
const ONLY = onlyIdx >= 0 ? new Set(argv[onlyIdx + 1].split(',')) : null;

// --- manifest ---
const manifestPath = join(__dirname, 'hero-image-manifest.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

// --- dirs ---
const BLOG_DIR = join(ROOT, 'src/content/blog');
const PUBLIC_DIR = join(ROOT, 'public/images/blog');
if (!existsSync(PUBLIC_DIR)) mkdirSync(PUBLIC_DIR, { recursive: true });

// --- frontmatter helpers ---
function parseFrontmatter(content) {
  const m = content.match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) return { frontmatter: '', body: content };
  return { frontmatter: m[1], body: content.slice(m[0].length) };
}

function hasHeroImage(frontmatter) {
  return /^heroImage:/m.test(frontmatter);
}

function setHeroImage(frontmatter, filename) {
  const path = `/images/blog/${filename}`;
  if (hasHeroImage(frontmatter)) {
    return frontmatter.replace(/^heroImage:.*$/m, `heroImage: ${path}`);
  }
  // Insert after pubDate for consistency with existing posts.
  const lines = frontmatter.split('\n');
  const idx = lines.findIndex((l) => /^pubDate:/.test(l));
  const insertAt = idx >= 0 ? idx + 1 : lines.length;
  lines.splice(insertAt, 0, `heroImage: ${path}`);
  return lines.join('\n');
}

// --- replicate ---
async function createPrediction(prompt, attempt = 1) {
  const res = await fetch(
    'https://api.replicate.com/v1/models/black-forest-labs/flux-1.1-pro/predictions',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${TOKEN}`,
        'Content-Type': 'application/json',
        Prefer: 'wait=60',
      },
      body: JSON.stringify({
        input: {
          prompt,
          aspect_ratio: '16:9',
          output_format: 'jpg',
          output_quality: 90,
          safety_tolerance: 2,
        },
      }),
    }
  );

  // Handle 429 throttling. Replicate caps free-tier accounts at 6 req/min
  // with a burst of 1 (when balance is under $5). The response includes a
  // retry_after hint in seconds — wait that long plus a small buffer.
  if (res.status === 429 && attempt <= 8) {
    let retryAfter = 6;
    try {
      const body = await res.clone().json();
      if (body?.retry_after) retryAfter = Number(body.retry_after);
    } catch {}
    const waitMs = (retryAfter + 1) * 1000;
    console.log(`    (throttled, waiting ${retryAfter + 1}s — attempt ${attempt}/8)`);
    await new Promise((r) => setTimeout(r, waitMs));
    return createPrediction(prompt, attempt + 1);
  }

  if (!res.ok) {
    throw new Error(`Replicate create ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

async function pollPrediction(getUrl) {
  const res = await fetch(getUrl, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) throw new Error(`Poll ${res.status}: ${await res.text()}`);
  return res.json();
}

async function generateImage(prompt) {
  let prediction = await createPrediction(prompt);
  while (prediction.status === 'starting' || prediction.status === 'processing') {
    await new Promise((r) => setTimeout(r, 2000));
    prediction = await pollPrediction(prediction.urls.get);
  }
  if (prediction.status !== 'succeeded') {
    throw new Error(`status=${prediction.status} error=${prediction.error ?? 'n/a'}`);
  }
  const url = Array.isArray(prediction.output) ? prediction.output[0] : prediction.output;
  if (!url) throw new Error(`No output URL: ${JSON.stringify(prediction).slice(0, 200)}`);
  return url;
}

async function downloadImage(url, dest) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  writeFileSync(dest, buf);
}

// Spawn the Python tear-mask generator for one slug. The BlogPost.astro
// hero applies a per-slug PNG mask via CSS — missing the PNG means the
// hero renders invisibly. Tying mask generation to image generation
// here ensures the two never drift out of sync.
function generateTearMask(slug) {
  const script = join(__dirname, 'generate-tear-mask.py');
  const res = spawnSync('python3', [script, slug], {
    cwd: ROOT,
    encoding: 'utf8',
  });
  if (res.status !== 0) {
    throw new Error(
      `tear-mask: ${res.stderr?.trim() || res.stdout?.trim() || 'unknown error'}`
    );
  }
  return res.stdout.trim();
}

// --- main ---
async function main() {
  const entries = Object.entries(manifest).filter(([k]) => !k.startsWith('_'));
  let generated = 0;
  let skipped = 0;
  let failed = 0;
  const failures = [];

  console.log(
    `Starting hero-image generation. dry-run=${DRY_RUN} force=${FORCE} only=${ONLY ? [...ONLY].join(',') : 'all'}\n`
  );

  for (const [slug, prompt] of entries) {
    if (ONLY && !ONLY.has(slug)) continue;

    const mdPath = join(BLOG_DIR, `${slug}.md`);
    if (!existsSync(mdPath)) {
      console.warn(`- skip ${slug} (no .md file)`);
      skipped++;
      continue;
    }

    const content = readFileSync(mdPath, 'utf8');
    const { frontmatter, body } = parseFrontmatter(content);

    // Only skip if BOTH the frontmatter heroImage is set AND the actual
    // JPG exists on disk. Otherwise we'd skip posts whose .md was
    // pre-populated with heroImage but never had the image generated.
    const expectedImagePath = join(PUBLIC_DIR, `${slug}.jpg`);
    if (hasHeroImage(frontmatter) && existsSync(expectedImagePath) && !FORCE) {
      console.log(`- skip ${slug} (already has heroImage + image on disk)`);
      skipped++;
      continue;
    }

    console.log(`→ ${slug}`);
    console.log(`  prompt: ${prompt.length > 100 ? prompt.slice(0, 97) + '…' : prompt}`);

    if (DRY_RUN) {
      console.log(`  [dry-run] would save to public/images/blog/${slug}.jpg`);
      generated++;
      continue;
    }

    try {
      const url = await generateImage(prompt);
      console.log(`  ✓ generated`);
      const dest = join(PUBLIC_DIR, `${slug}.jpg`);
      await downloadImage(url, dest);
      console.log(`  ✓ saved public/images/blog/${slug}.jpg`);

      const newFrontmatter = setHeroImage(frontmatter, `${slug}.jpg`);
      writeFileSync(mdPath, `---\n${newFrontmatter}\n---\n${body}`);
      console.log(`  ✓ updated frontmatter`);

      if (!SKIP_MASK) {
        try {
          generateTearMask(slug);
          console.log(`  ✓ generated tear mask`);
        } catch (err) {
          console.warn(`  ! tear-mask failed (image still saved): ${err.message}`);
        }
      }

      generated++;

      // Stay comfortably under the 6/min Replicate rate cap (10s spacing
      // between successful creates). Skipped on the last iteration so we
      // don't waste 10s after the final image.
      const remaining = entries.filter(
        ([s]) => (!ONLY || ONLY.has(s)) && s !== slug
      );
      if (remaining.length > 0) {
        await new Promise((r) => setTimeout(r, 10000));
      }
    } catch (err) {
      console.error(`  ✗ ${err.message}`);
      failures.push([slug, err.message]);
      failed++;
    }
  }

  console.log(`\nDone. generated=${generated} skipped=${skipped} failed=${failed}`);
  if (failures.length) {
    console.log('\nFailures:');
    for (const [slug, msg] of failures) console.log(`  ${slug}: ${msg}`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
