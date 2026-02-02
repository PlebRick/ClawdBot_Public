const fs = require('fs');
const path = require('path');
const { BrowserSession } = require('../lib/session');

const BASE_URL = 'https://www.gospeltruth.net';

// Known entry points
const KNOWN_PAGES = {
  home: '/index.htm',
  works: '/cgfworks.htm',
  sermons: '/sermindex.htm',
  subjects: '/subjectindex.htm',
  scripture: '/ot_nt_search_page.htm',
  life: '/life_of_finney.htm',
  timeline: '/finneychronology.htm',
  glossary: '/glossary.htm',
  letters: '/Finneyletters/finletindices/finneylettersindex.htm',
  selected: '/selected_sermons.htm',
  oberlin: '/oe/OEmainindex.htm',
  audio: '/mp3generalindex.htm',
  others: '/others.htm',
};

// Subject index anchors
const SUBJECTS = {
  god: '#God',
  jesus: '#JESUS%20CHRIST',
  'holy-spirit': '#Holy%20Spirit',
  faith: '#Faith',
  holiness: '#Holiness',
  prayer: '#Prayer',
  wicked: '#The%20Wicked',
  'true-false': '#True%20and%20False',
};

/**
 * Create a Finney browser session. No auth needed.
 */
async function createSession() {
  const session = new BrowserSession({ minDelay: 2000 });
  await session.launch();
  return session;
}

/**
 * Navigate to a known page or URL path.
 */
async function navigateTo(session, target) {
  let urlPath;
  if (KNOWN_PAGES[target]) {
    urlPath = KNOWN_PAGES[target];
  } else if (SUBJECTS[target]) {
    urlPath = '/subjectindex.htm' + SUBJECTS[target];
  } else {
    urlPath = target;
  }
  const url = urlPath.startsWith('http') ? urlPath : BASE_URL + urlPath;
  await session.goto(url, { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 2000));
  return { ok: true, url: session.page.url() };
}

/**
 * Search the sermon index for a topic/keyword.
 * Since the site has no search, we load the index and filter links by text.
 */
async function searchSermons(query) {
  const session = await createSession();
  try {
    await navigateTo(session, 'sermons');
    
    const results = await session.page.evaluate((q) => {
      const qLower = q.toLowerCase();
      const qTerms = qLower.split(/\s+/);
      return Array.from(document.querySelectorAll('a'))
        .map(a => ({ text: a.textContent.trim(), href: a.href }))
        .filter(l => {
          if (!l.text || l.text.length < 3) return false;
          const tLower = l.text.toLowerCase();
          return qTerms.every(t => tLower.includes(t));
        })
        .reduce((acc, l) => {
          if (!acc.find(x => x.href === l.href)) acc.push(l);
          return acc;
        }, [])
        .slice(0, 30);
    }, query);
    
    return { results, query, source: 'sermon-index' };
  } finally {
    await session.close();
  }
}

/**
 * Search the subject index for a topic.
 */
async function searchSubjects(query) {
  const session = await createSession();
  try {
    await navigateTo(session, 'subjects');
    
    const results = await session.page.evaluate((q) => {
      const qLower = q.toLowerCase();
      const qTerms = qLower.split(/\s+/);
      return Array.from(document.querySelectorAll('a'))
        .map(a => ({ text: a.textContent.trim(), href: a.href }))
        .filter(l => {
          if (!l.text || l.text.length < 3 || !l.href.includes('gospeltruth')) return false;
          const tLower = l.text.toLowerCase();
          return qTerms.some(t => tLower.includes(t));
        })
        .reduce((acc, l) => {
          if (!acc.find(x => x.href === l.href)) acc.push(l);
          return acc;
        }, [])
        .slice(0, 30);
    }, query);
    
    return { results, query, source: 'subject-index' };
  } finally {
    await session.close();
  }
}

/**
 * Search by scripture reference — find Finney sermons on a given text.
 */
async function searchScripture(query) {
  const session = await createSession();
  try {
    await navigateTo(session, 'scripture');
    
    // The scripture page links to sub-pages (OT books, NT books)
    // First get the sub-page links
    const subPages = await session.page.evaluate(() => {
      return Array.from(document.querySelectorAll('a'))
        .map(a => ({ text: a.textContent.trim(), href: a.href }))
        .filter(l => l.href.includes('gospeltruth') && l.text.length > 2)
        .reduce((acc, l) => { if (!acc.find(x => x.href === l.href)) acc.push(l); return acc; }, []);
    });
    
    // Search query across sub-page link text
    const qLower = query.toLowerCase();
    const matches = subPages.filter(l => l.text.toLowerCase().includes(qLower));
    
    if (matches.length > 0) {
      return { results: matches.slice(0, 20), query, source: 'scripture-index' };
    }
    
    // If no direct match, try navigating to NT or OT sub-pages and searching there
    // For now return the top-level structure
    return { results: subPages.slice(0, 20), query, source: 'scripture-index', note: 'No direct match — showing index structure' };
  } finally {
    await session.close();
  }
}

/**
 * Read a specific sermon/lecture page and extract its text content.
 */
async function readPage(urlOrPath) {
  const session = await createSession();
  try {
    const url = urlOrPath.startsWith('http') ? urlOrPath : BASE_URL + '/' + urlOrPath;
    await session.goto(url, { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 2000));
    
    const content = await session.page.evaluate(() => ({
      url: window.location.href,
      title: document.title,
      text: document.body?.innerText?.substring(0, 10000) || '',
    }));
    
    return content;
  } finally {
    await session.close();
  }
}

/**
 * Combined search — searches sermons and subjects simultaneously.
 */
async function search(query) {
  const [sermons, subjects] = await Promise.all([
    searchSermons(query),
    searchSubjects(query),
  ]);
  
  return {
    query,
    sermons: sermons.results,
    subjects: subjects.results,
    totalResults: sermons.results.length + subjects.results.length,
  };
}

module.exports = {
  createSession, navigateTo, searchSermons, searchSubjects,
  searchScripture, readPage, search,
  KNOWN_PAGES, SUBJECTS,
};

// CLI
if (require.main === module) {
  const query = process.argv[2] || 'prayer';
  const mode = process.argv[3] || 'search'; // search, sermons, subjects, scripture, read
  
  console.log(`Finney (${mode}): "${query}"...`);
  
  const fn = {
    search, sermons: searchSermons, subjects: searchSubjects,
    scripture: searchScripture, read: readPage,
  }[mode] || search;
  
  fn(query).then(data => {
    if (data.sermons) {
      console.log(`\nSermons (${data.sermons.length}):`);
      data.sermons.forEach(r => console.log(`  ${r.text.substring(0, 80)} → ${r.href}`));
      console.log(`\nSubjects (${data.subjects.length}):`);
      data.subjects.forEach(r => console.log(`  ${r.text.substring(0, 80)} → ${r.href}`));
    } else if (data.results) {
      console.log(`\nResults (${data.results.length}):`);
      data.results.forEach(r => console.log(`  ${r.text?.substring(0, 80) || ''} → ${r.href || ''}`));
    } else if (data.text) {
      console.log(`\nTitle: ${data.title}`);
      console.log(`Text: ${data.text.substring(0, 500)}`);
    }
    console.log(JSON.stringify(data, null, 2).substring(0, 200) + '...');
  }).catch(console.error);
}
