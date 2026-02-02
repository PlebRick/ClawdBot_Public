const fs = require('fs');
const path = require('path');
const { BrowserSession } = require('../lib/session');

const COOKIES_PATH = path.join(__dirname, '..', 'cookies', 'logos-cookies.json');
const BASE_URL = 'https://app.logos.com';

// Search kinds supported by Logos
const SEARCH_KINDS = {
  all: 'all',
  books: 'books',
  bible: 'bible',
  factbook: 'factbook',
  morph: 'morph',
  media: 'media',
  maps: 'maps',
};

/**
 * Create an authenticated Logos browser session.
 */
async function createSession() {
  const cookies = JSON.parse(fs.readFileSync(COOKIES_PATH, 'utf8'));
  const session = new BrowserSession({ minDelay: 2000 });
  await session.launch(cookies);
  return session;
}

/**
 * Search Rick's Logos library.
 * @param {string} query - Search query
 * @param {string} kind - Search kind: 'books' (default), 'bible', 'factbook', 'all'
 * @returns {{ results: Array, count: string, synopsis: string|null }}
 */
async function search(query, kind = 'books') {
  const session = await createSession();
  try {
    const encodedQuery = encodeURIComponent(query);
    const searchKind = SEARCH_KINDS[kind] || 'books';
    const url = `${BASE_URL}/search?kind=${searchKind}&q=${encodedQuery}&resources=allResources&syntax=v2`;

    await session.goto(url, { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 12000));

    // Check for login redirect
    if (session.page.url().includes('login') || session.page.url().includes('signin')) {
      return { error: 'Session expired — Rick needs to re-login on Chrome', results: [], count: '0' };
    }

    // Extract results from divs containing the search terms
    const data = await session.page.evaluate((q) => {
      const queryTerms = q.toLowerCase().split(/\s+/);

      // Get result count
      const allText = document.body?.innerText || '';
      const countMatch = allText.match(/Results?\s+(\d+[-–]\d+|\d+)/i);
      const count = countMatch ? countMatch[0] : 'unknown';

      // Extract result divs — look for content containing query terms
      const divs = Array.from(document.querySelectorAll('div'));
      const results = [];
      const seen = new Set();

      for (const div of divs) {
        const text = div.innerText?.trim();
        if (!text || text.length < 20 || text.length > 2000) continue;
        if (div.children.length > 10) continue;

        const lower = text.toLowerCase();
        const hasQueryTerm = queryTerms.some(t => lower.includes(t));
        if (!hasQueryTerm) continue;

        // Skip nav/UI elements
        if (lower.startsWith('skip to') || lower.startsWith('dashboard')) continue;

        // Deduplicate by first 100 chars
        const key = text.substring(0, 100);
        if (seen.has(key)) continue;
        seen.add(key);

        // Check if this looks like a result with a source citation
        const hasSource = text.includes(',') && (text.includes('p ') || text.includes('vol') || text.includes('('));

        results.push({
          text: text.substring(0, 500),
          isSourceCitation: hasSource && text.length < 200,
        });
      }

      // Look for synopsis (AI-generated summary)
      const synopsisEl = Array.from(document.querySelectorAll('div')).find(d => {
        const t = d.innerText?.trim();
        return t && t.startsWith('Synopsis') && t.length > 20;
      });
      const synopsis = synopsisEl ? synopsisEl.innerText.replace('Synopsis\n', '').trim() : null;

      return { results: results.slice(0, 30), count, synopsis };
    }, query);

    return data;
  } finally {
    await session.close();
  }
}

/**
 * Open a specific book by its Logos resource ID.
 * @param {string} resourceId - e.g., 'LLS:CARSONSRMNRCHV'
 */
async function openBook(resourceId) {
  const session = await createSession();
  try {
    const url = `${BASE_URL}/books/${resourceId}`;
    await session.goto(url, { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 10000));

    const content = await session.page.evaluate(() => ({
      url: window.location.href,
      title: document.title,
      text: document.body?.innerText?.substring(0, 5000) || '',
    }));

    return content;
  } finally {
    await session.close();
  }
}

/**
 * Search the library catalog (find books by title/author).
 * Uses the Library tab's "Find" input.
 */
async function searchLibrary(query) {
  const session = await createSession();
  try {
    await session.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 8000));

    // Find the library 'Find' input
    const findInput = await session.page.$('input[name="query"]');
    if (findInput) {
      await findInput.click();
      await findInput.fill(query);
      await new Promise(r => setTimeout(r, 3000));

      // Extract matching resources
      const results = await session.page.evaluate((q) => {
        const divs = Array.from(document.querySelectorAll('div'));
        const qLower = q.toLowerCase();
        return divs
          .map(d => d.innerText?.trim())
          .filter(t => t && t.length > 5 && t.length < 300 && t.toLowerCase().includes(qLower))
          .reduce((acc, t) => { if (!acc.includes(t)) acc.push(t); return acc; }, [])
          .slice(0, 30);
      }, query);

      return { results, query };
    }

    return { results: [], query, error: 'Find input not found' };
  } finally {
    await session.close();
  }
}

/**
 * Take a screenshot of the current Logos view.
 */
async function screenshot(session, filename) {
  const outDir = path.join(__dirname, '..', 'output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, filename || `logos-${Date.now()}.png`);
  await session.page.screenshot({ path: outPath, fullPage: false });
  return outPath;
}

module.exports = { createSession, search, openBook, searchLibrary, screenshot, SEARCH_KINDS };

// CLI test
if (require.main === module) {
  const query = process.argv[2] || 'atonement';
  const kind = process.argv[3] || 'books';
  console.log(`Searching Logos (${kind}): "${query}"...`);
  search(query, kind).then(data => {
    console.log(`\nCount: ${data.count}`);
    if (data.synopsis) console.log(`\nSynopsis: ${data.synopsis.substring(0, 300)}`);
    console.log(`\nResults (${data.results.length}):`);
    data.results.forEach((r, i) => {
      console.log(`\n--- Result ${i + 1} ---`);
      console.log(r.text.substring(0, 300));
    });
  }).catch(console.error);
}
