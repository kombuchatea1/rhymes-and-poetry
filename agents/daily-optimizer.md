# Daily blog optimizer agent

## Purpose

Once a day, pick one blog post on R&P. Analyze it for SEO and structural improvements. Open a pull request with proposed changes plus a clear explanation of what was changed and why. Human reviews and merges.

## Status

**Designed, not yet implemented.** Designed in conversation on 2026-05-21. Build target: after the immediate site improvements ship (favicons, OG card, sitemap submission, reading time, related posts).

## Workflow

```
GitHub Actions cron (daily 06:00 UTC)
  → Pick next post (oldest `optimizedAt` frontmatter, or missing)
  → Build "site context" (all post slugs + titles + categories — for internal-link suggestions)
  → Call Claude API with post + context + optimization rules
  → Receive structured JSON response (changes + reasoning)
  → Open PR with diff + summary
  → GitHub notifies Jake
  → Jake reviews, merges or closes
```

## What it can change

**Allowed:**

- `title` (target 50–60 chars for SEO)
- `description` (140–160 chars, includes primary keyword naturally — without sounding stuffed)
- Internal links inside prose intros and outros (1–3 contextual links to related posts)
- Image alt text on any inline images (rare for poetry — heroes already have `alt=""` empty by design)
- `heroImage` (only if missing — should never happen in practice now)
- Add `optimizedAt: YYYY-MM-DD` to frontmatter after run

**Forbidden:**

- The poem body inside `<div class="poem-block">` — canonical, never auto-edit
- The `— JTC` signature block
- `pubDate`
- `category`
- The prose voice — agent can add an internal link inside an existing sentence, never rewrite the sentence
- Adding new sections or restructuring the post

## Selection logic

```pseudocode
posts = all_posts_in_blog_dir
candidates = posts WHERE optimizedAt IS NULL
              OR optimizedAt IS OLDEST
pick first from candidates
```

This naturally cycles through the catalog. With ~146 posts on daily runs, each post gets re-optimized roughly every 5 months.

## Cost estimate

- Claude Sonnet input: ~3–8k tokens per run (post + site context)
- Claude Sonnet output: ~500–1500 tokens (changes + reasoning)
- Per-run cost: ~$0.05–$0.15
- Monthly: ~$2–5

Trivially affordable. The expensive part is human review time, so design the PR summary to make review fast.

## Implementation TODO (when we build it)

- [ ] Add `optimizedAt: z.coerce.date().optional()` to `src/content.config.ts` blog schema
- [ ] Create `scripts/optimize-post.ts` (the agent runner)
- [ ] Create `scripts/lib/build-site-context.ts` (generates the index of posts for internal-link suggestions)
- [ ] Create `.github/workflows/daily-optimizer.yml` (cron + secrets + PR creation)
- [ ] Add `ANTHROPIC_API_KEY` to repo secrets
- [ ] First-run test on a single post manually (don't enable cron yet)
- [ ] Tune the system prompt over the first 5–10 runs based on PR quality
- [ ] Enable cron once Jake is satisfied with the change quality

## Open design questions

- **No-op behavior:** if the agent finds no meaningful improvements, should it skip opening a PR? (Probably yes — log a "no changes recommended" note instead. Avoids review noise.)
- **PR cap:** max 3 unmerged optimizer PRs at once. If at cap, skip the run. (Prevents pileup if Jake is on vacation.)
- **Auto-merge for ultra-safe changes** (e.g., adding missing alt text): not in v1. Start with all-human-review. Maybe add later for explicitly safe categories.
- **Internal link quality control:** the agent should only suggest internal links where the linked post's *topic* directly matches the linking sentence's *topic*. No keyword-stuffing links.

## Why this is the right first agent

Contained, repeatable, reviewable, has clear measurable output (PRs shipped / week). The site grows in quality over time without daily intervention. It's exactly the kind of pattern an agency would offer to clients ("we'll keep your blog SEO-current with daily optimization runs reviewed by you") — building it for R&P is also building the agency demo.
