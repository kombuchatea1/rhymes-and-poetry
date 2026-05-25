/**
 * src/data/quotes.js
 * Rhymes & Poetry — daily rotating featured quote pool
 *
 * getTodaysQuote() is called at build time from Hero.astro.
 * A small client-side script in Hero.astro also calls it in the browser,
 * so the correct quote always shows even on a stale build.
 *
 * To add more quotes: append to the QUOTES array below.
 * Pool size can be any number — rotation uses dayOfYear % QUOTES.length.
 */

export const QUOTES = [
  {
    quote: "Two roads diverged in a wood, and I—\nI took the one less traveled by,\nAnd that has made all the difference.",
    author: "Robert Frost",
    source: "The Road Not Taken (1916)",
  },
  {
    quote: "Hope is the thing with feathers\nThat perches in the soul,\nAnd sings the tune without the words,\nAnd never stops at all.",
    author: "Emily Dickinson",
    source: "\"Hope\" is the thing with feathers (c. 1861)",
  },
  {
    quote: "Do not go gentle into that good night.\nRage, rage against the dying of the light.",
    author: "Dylan Thomas",
    source: "Do Not Go Gentle into That Good Night (1951)",
  },
  {
    quote: "I am large, I contain multitudes.",
    author: "Walt Whitman",
    source: "Song of Myself (1855)",
  },
  {
    quote: "Beauty is truth, truth beauty,—that is all\nYe know on earth, and all ye need to know.",
    author: "John Keats",
    source: "Ode on a Grecian Urn (1819)",
  },
  {
    quote: "Tell me, what is it you plan to do\nwith your one wild and precious life?",
    author: "Mary Oliver",
    source: "The Summer Day (1990)",
  },
  {
    quote: "I have measured out my life with coffee spoons.",
    author: "T.S. Eliot",
    source: "The Love Song of J. Alfred Prufrock (1915)",
  },
  {
    quote: "April is the cruellest month, breeding\nLilacs out of the dead land.",
    author: "T.S. Eliot",
    source: "The Waste Land (1922)",
  },
  {
    quote: "She walks in beauty, like the night\nOf cloudless climes and starry skies.",
    author: "Lord Byron",
    source: "She Walks in Beauty (1814)",
  },
  {
    quote: "What happens to a dream deferred?\nDoes it dry up like a raisin in the sun?",
    author: "Langston Hughes",
    source: "Harlem (1951)",
  },
  {
    quote: "Hold fast to dreams,\nFor if dreams die,\nLife is a broken-winged bird\nThat cannot fly.",
    author: "Langston Hughes",
    source: "Dreams (1922)",
  },
  {
    quote: "I am the master of my fate,\nI am the captain of my soul.",
    author: "William Ernest Henley",
    source: "Invictus (1888)",
  },
  {
    quote: "How do I love thee? Let me count the ways.\nI love thee to the depth and breadth and height\nMy soul can reach.",
    author: "Elizabeth Barrett Browning",
    source: "Sonnets from the Portuguese, No. 43 (1850)",
  },
  {
    quote: "Because I could not stop for Death—\nHe kindly stopped for me—\nThe Carriage held but just Ourselves—\nAnd Immortality.",
    author: "Emily Dickinson",
    source: "Because I could not stop for Death (c. 1863)",
  },
  {
    quote: "I dwell in Possibility—\nA fairer House than Prose—",
    author: "Emily Dickinson",
    source: "I dwell in Possibility (c. 1862)",
  },
  {
    quote: "Quoth the Raven, 'Nevermore.'",
    author: "Edgar Allan Poe",
    source: "The Raven (1845)",
  },
  {
    quote: "No man is an island,\nEntire of itself;\nEvery man is a piece of the continent,\nA part of the main.",
    author: "John Donne",
    source: "Meditation XVII (1624)",
  },
  {
    quote: "Shall I compare thee to a summer's day?\nThou art more lovely and more temperate.",
    author: "William Shakespeare",
    source: "Sonnet 18 (1609)",
  },
  {
    quote: "I wandered lonely as a cloud\nThat floats on high o'er vales and hills.",
    author: "William Wordsworth",
    source: "I Wandered Lonely as a Cloud (1807)",
  },
  {
    quote: "A thing of beauty is a joy for ever:\nIts loveliness increases; it will never\nPass into nothingness.",
    author: "John Keats",
    source: "Endymion (1818)",
  },
  {
    quote: "Water, water, every where,\nNor any drop to drink.",
    author: "Samuel Taylor Coleridge",
    source: "The Rime of the Ancient Mariner (1798)",
  },
  {
    quote: "Gather ye rosebuds while ye may,\nOld Time is still a-flying;\nAnd this same flower that smiles today\nTo-morrow will be dying.",
    author: "Robert Herrick",
    source: "To the Virgins, to Make Much of Time (1648)",
  },
  {
    quote: "I celebrate myself, and sing myself,\nAnd what I assume you shall assume,\nFor every atom belonging to me as good belongs to you.",
    author: "Walt Whitman",
    source: "Song of Myself (1855)",
  },
  {
    quote: "If you can keep your head when all about you\nAre losing theirs and blaming it on you—\nYours is the Earth and everything that's in it.",
    author: "Rudyard Kipling",
    source: "If— (1910)",
  },
  {
    quote: "Once upon a midnight dreary, while I pondered, weak and weary,\nOver many a quaint and curious volume of forgotten lore—",
    author: "Edgar Allan Poe",
    source: "The Raven (1845)",
  },
  {
    quote: "Yet each man kills the thing he loves,\nBy each let this be heard,\nSome do it with a bitter look,\nSome with a flattering word.",
    author: "Oscar Wilde",
    source: "The Ballad of Reading Gaol (1898)",
  },
  {
    quote: "The woods are lovely, dark and deep,\nBut I have promises to keep,\nAnd miles to go before I sleep.",
    author: "Robert Frost",
    source: "Stopping by Woods on a Snowy Evening (1923)",
  },
  {
    quote: "Come live with me and be my love,\nAnd we will all the pleasures prove.",
    author: "Christopher Marlowe",
    source: "The Passionate Shepherd to His Love (1599)",
  },
  {
    quote: "You do not have to be good.\nYou only have to let the soft animal of your body\nlove what it loves.",
    author: "Mary Oliver",
    source: "Wild Geese (1986)",
  },
  {
    quote: "Poetry is the shadow cast by our streetlight imaginations.",
    author: "Lawrence Ferlinghetti",
    source: "Poetry as Insurgent Art (2007)",
  },
];

/**
 * Returns today's quote based on the current UTC date.
 * Deterministic: same quote all day, rotates at midnight UTC.
 *
 * @returns {{ quote: string, author: string, source: string }}
 */
export function getTodaysQuote() {
  const now = new Date();
  const dayOfYear = Math.floor(
    (Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()) -
      Date.UTC(now.getUTCFullYear(), 0, 0)) /
      86400000
  );
  return QUOTES[dayOfYear % QUOTES.length];
}
