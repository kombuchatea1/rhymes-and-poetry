# Rhymes & Poetry — Claude operational notes

**The site:** rhymesandpoetry.org (rhymesandpoetry.com pending Wix→Porkbun transfer). Personal poetry brand by Jake Cohn (JTC). Astro + Cloudflare Workers. ~146 poems migrated from IG.

**Secondary purpose:** R&P is the proof-of-work for an AI agency Jake is building with his wife — every script, workflow, and pattern we build here is potential agency IP. Build with reusability in mind when reasonable.

## Brand voice

**Yes:** reflective, plainspoken, emotionally specific, warm, honest. The closing line `— JTC` matters. Conversational asides like "kinda cool" and "thanks for reading" land because they sound like a person, not a brand.

**No:** marketing copy, generic motivational language, "unlock / unleash / tapestry / elevate / realm / embark." Don't refer to poems as "content" — use "poems," "pieces," or "writing." No AI-tells: "delve, leveraging, in conclusion, it's important to note."

## Hard rules

- **Never edit the inside of a `<div class="poem-block">`** — that's canonical poem text
- **Never edit a `<div class="signature">` block** — that's the `— JTC` ornament
- Never touch a post's `pubDate` without asking
- Hero image / tear mask / frontmatter must match the slug exactly:
  `<slug>.md` → `/images/blog/<slug>.jpg` + `/torn-masks/<slug>.png`
- Don't auto-commit. Show changes for review before pushing
- Use TodoWrite for non-trivial tasks; small single-file edits don't need it

## Current state (last updated 2026-05-21)

- 146 poems live with hero images + per-post torn-paper masks
- About page rewritten in Jake's voice
- Subscribe form → `/api/subscribe` endpoint → forwards to Buttondown (`NEWSLETTER_USERNAME = "jtc28"`)
- Favicon family + 1200×630 OG card generated
- DNS: **.org** is live via Cloudflare Registrar. **.com** transfer Wix→Porkbun in progress (~5-7 days). After transfer completes, switch nameservers at Porkbun to Cloudflare's
- Pending: submit sitemap to Search Console; build daily optimizer agent; add reading time + related posts; analytics

## Common commands

```bash
npm run dev                                # local dev server
npm run build                              # production build
npm run preview                            # build + wrangler dev
npm run deploy                             # build + wrangler deploy

node scripts/generate-hero-images.mjs      # generate missing hero images via Replicate Flux
python3 scripts/generate-tear-mask.py SLUG # torn-paper mask for a post
python3 scripts/generate-logo.py           # regenerate favicon family + OG card
```

## File conventions

```
src/content/blog/        - poem posts (.md with frontmatter)
src/content.config.ts    - blog post schema (zod validated)
src/components/          - reusable .astro components
src/layouts/             - page layouts (BlogPost.astro)
src/pages/               - routes (about, subscribe, etc.)
src/pages/api/           - Astro server endpoints
src/styles/global.css    - design tokens (--rp-sage, --rp-cream, etc.)
src/consts/              - canonical constants (newsletter config, topic defs)
public/images/blog/      - hero images (one per post slug)
public/images/brand/     - logo + OG card
public/torn-masks/       - per-post torn-paper PNGs
scripts/                 - one-shot utilities
```

## Brand colors + type

- Sage `#4a6741` | Sage-dark `#3b5434` | Sage-soft `rgba(74,103,65,0.08)`
- Cream `#faf9f6` | Cream-warm `#f0eee6`
- Display font: Playfair Display (italic for poetry blocks + signatures)
- Body font: Atkinson (loaded locally via Astro font integration)

## Strategy + agency context

Detailed strategy lives in `/strategy/`:

- `brand-positioning.md` — voice and positioning
- `audiences.md` — who R&P is for
- `content-pillars.md` — categories and what fits where
- `monetization-roadmap.md` — long-term revenue paths
- `agency-vision.md` — the bigger plan (Jake + wife, agency build)

Agent specs in `/agents/` as they get built:

- `daily-optimizer.md` — designed, not yet implemented
