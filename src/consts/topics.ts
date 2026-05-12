/* ===========================================================================
 * src/consts/topics.ts
 * Rhymes & Poetry — canonical topic definitions
 *
 * Single source of truth for the 5 categories. Imported by:
 *   - src/components/Topics.astro       (home page counters)
 *   - src/pages/topics/index.astro      (topics overview)
 *   - src/pages/topics/[slug].astro     (individual topic pages)
 *
 * If you change a slug here, ALSO update the z.enum() in
 * src/content.config.ts to match — they are coupled by design but
 * TypeScript can't enforce the link across files. Either change both
 * together or risk runtime mismatches.
 *
 * Why this lives in its own module rather than as a const at the top
 * of [slug].astro: Astro's getStaticPaths() runs in an isolated
 * execution context that doesn't see same-file frontmatter constants.
 * Importing from a separate module is the canonical pattern.
 * ========================================================================= */

export const TOPIC_DEFS = [
	{
		slug: "reflections",
		label: "Reflections",
		desc: "Personal observations, meditations on character and growth — the quiet pieces.",
	},
	{
		slug: "rap-and-bars",
		label: "Rap & Bars",
		desc: "Lyrics and bars built for cadence, force, and timing.",
	},
	{
		slug: "nature",
		label: "Nature",
		desc: "The natural world as mirror and metaphor.",
	},
	{
		slug: "love-loss",
		label: "Love & Loss",
		desc: "What we hold, what we give up, what stays after.",
	},
	{
		slug: "community",
		label: "Community",
		desc: "Stories from the people, places, and moments that shape us.",
	},
] as const;

export type TopicSlug = (typeof TOPIC_DEFS)[number]["slug"];
