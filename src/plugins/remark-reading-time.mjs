import getReadingTime from 'reading-time';
import { toString } from 'mdast-util-to-string';

/**
 * Remark plugin — injects `minutesRead` into each post's frontmatter at
 * build time. Accessed in [...slug].astro via remarkPluginFrontmatter.
 *
 * reading-time returns e.g. "3 min read" based on ~200 wpm average.
 * For poems this will often be "1 min read" — that's fine and accurate.
 */
export function remarkReadingTime() {
  return function (tree, { data }) {
    const textOnPage = toString(tree);
    const readingTime = getReadingTime(textOnPage);
    data.astro.frontmatter.minutesRead = readingTime.text;
  };
}
