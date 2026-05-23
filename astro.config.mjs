// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig, fontProviders, passthroughImageService } from 'astro/config';
import { remarkReadingTime } from './src/plugins/remark-reading-time.mjs';

import cloudflare from '@astrojs/cloudflare';

// https://astro.build/config
export default defineConfig({
  // Production canonical URL — used by Astro.site for absolute URLs in
  // OG/Twitter meta tags, sitemap, and RSS feed. While the Wix→Porkbun
  // transfer of rhymesandpoetry.com is pending, point at the .org variant
  // (active via Cloudflare Registrar). Switch to rhymesandpoetry.com once
  // the .com DNS resolves to this Worker.
  site: 'https://rhymesandpoetry.org',
  integrations: [mdx(), sitemap()],

  markdown: {
    remarkPlugins: [remarkReadingTime],
  },

  // Image service: passthrough (serve originals, no runtime transformation).
  // Reason: @astrojs/cloudflare doesn't include image transformation in the
  // free tier — without this, deployed builds 404 on /_image URLs and
  // images break on the live site. passthroughImageService() ships the
  // original asset bytes as-is, which works everywhere.
  // Trade-off: no automatic WebP/AVIF conversion or responsive variants.
  // Responsive `widths` and `sizes` attributes on Image components are
  // ignored — the original is always served. Source images should be
  // pre-optimized for size if needed.
  // Long-term upgrade path: enable Cloudflare Image Transformations
  // ($5/month) and switch to a Cloudflare-native image service.
  image: {
    service: passthroughImageService(),
  },

  fonts: [
      {
          provider: fontProviders.local(),
          name: 'Atkinson',
          cssVariable: '--font-atkinson',
          fallbacks: ['sans-serif'],
          options: {
              variants: [
                  {
                      src: ['./src/assets/fonts/atkinson-regular.woff'],
                      weight: 400,
                      style: 'normal',
                      display: 'swap',
                  },
                  {
                      src: ['./src/assets/fonts/atkinson-bold.woff'],
                      weight: 700,
                      style: 'normal',
                      display: 'swap',
                  },
              ],
          },
      },
	],

  adapter: cloudflare(),
});