import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const blog = defineCollection({
	// Load Markdown and MDX files in the `src/content/blog/` directory.
	loader: glob({ base: './src/content/blog', pattern: '**/*.{md,mdx}' }),
	// Type-check frontmatter using a schema
	schema: ({ image }) =>
		z.object({
			title: z.string(),
			description: z.string(),
			// Transform string to Date object
			pubDate: z.coerce.date(),
			updatedDate: z.coerce.date().optional(),
			// heroImage is now a string path under /public (e.g.
			// "/images/blog/foo.jpg"). Switched from image() to z.string()
			// because the Cloudflare Workers adapter's image transformation
			// pipeline is gated behind paid Cloudflare Image Transformations.
			// Public folder paths are served directly by the Workers static
			// asset handler — no transformation, no /_image URL wrapping,
			// guaranteed to work.
			heroImage: z.string().optional(),
			ig_shortcode: z.string().optional(),
			// Category — one of the five canonical topics. z.enum gives
			// us compile-time validation: a typo in a post's frontmatter
			// will fail the build rather than silently miscategorizing.
			category: z
				.enum([
					"reflections",
					"rap-and-bars",
					"nature",
					"love-loss",
					"community",
				])
				.optional(),
		}),
});

export const collections = { blog };
