# scripts/

Maintenance scripts for the Rhymes & Poetry site. None of these are part of the Astro build — they're one-shot or batch utilities run by hand.

## generate-hero-images.mjs

Generates hero images for blog posts via Replicate Flux 1.1 Pro.

**Requires:** `REPLICATE_API_TOKEN` in `.env` at the project root (gitignored).

**Inputs:** prompts in `scripts/hero-image-manifest.json` keyed by post slug.

**Outputs:**

- JPEGs written to `public/images/blog/{slug}.jpg`
- Frontmatter of `src/content/blog/{slug}.md` updated to include `heroImage: /images/blog/{slug}.jpg`
- Per-slug torn-paper mask PNG written to `public/torn-masks/{slug}.png` (via `generate-tear-mask.py` — required for the hero to render; the BlogPost layout applies it as a CSS mask)

**Usage:**

```bash
# generate every poem in the manifest that doesn't yet have heroImage
node scripts/generate-hero-images.mjs

# log the plan without calling the API
node scripts/generate-hero-images.mjs --dry-run

# run for a subset
node scripts/generate-hero-images.mjs --only namaste,frozen-in-time

# regenerate even if a heroImage is already wired up
node scripts/generate-hero-images.mjs --force --only spreading-peace

# generate images only, skip the python tear-mask step
node scripts/generate-hero-images.mjs --skip-mask
```

**Dependencies:** Node 22+ (project minimum) and Python 3 with Pillow + numpy (for the tear-mask subprocess). If Python isn't available, pass `--skip-mask` and run `python3 scripts/generate-tear-mask.py <slug>` separately on a machine that has it.

**Cost:** Flux 1.1 Pro is ~$0.04 per image as of mid-2025.

**After a successful run:** rotate the Replicate token. The comment in `.env` enforces this.

## generate-tear-mask.py

(Existing — see file header.)
