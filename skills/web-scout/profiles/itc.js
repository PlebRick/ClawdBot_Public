const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const FIREBASE_PATH = path.join(__dirname, '..', 'cookies', 'itc-firebase.json');
const BASE_URL = 'https://app.intothecryptoverse.com';

// Known high-value pages
const KNOWN_PAGES = {
  dashboard: '/dashboard',
  charts: '/charts',
  risk: '/charts/risk',
  'risk-levels': '/charts/risk-levels',
  dominance: '/charts/dominance',
  'fear-greed': '/charts/fear-greed-index',
  mvrv: '/charts/mvrv',
  'mvrv-z': '/charts/mvrv-z-score',
  nupl: '/charts/nupl',
  sopr: '/charts/sopr',
  'interest-rate': '/charts/interest-rate',
  recession: '/charts/interest-rate', // recession data is under interest-rate/macro
  inflation: '/charts/interest-rate', // same macro section
  'log-regression': '/charts/logarithmic-regression',
  'bull-market-support': '/charts/bull-market-support-band',
  'pi-cycle': '/charts/pi-cycle-bottom-top',
  'hash-ribbons': '/charts/hash-ribbons',
  'bubble-risk': '/charts/short-term-bubble-risk',
  'btc-risk': '/assets/bitcoin/risk',
  'sp500-risk': '/assets/SP500/risk',
  'gold-risk': '/assets/gold/risk',
  'dxy-risk': '/assets/dxy/risk',
};

function getFirebaseAuth() {
  return JSON.parse(fs.readFileSync(FIREBASE_PATH, 'utf8'));
}

function buildInitScript(auth) {
  return `(function(){var r=indexedDB.open("firebaseLocalStorageDb",1);r.onupgradeneeded=function(e){var d=e.target.result;if(!d.objectStoreNames.contains("firebaseLocalStorage"))d.createObjectStore("firebaseLocalStorage")};r.onsuccess=function(e){var d=e.target.result;try{var t=d.transaction("firebaseLocalStorage","readwrite");t.objectStore("firebaseLocalStorage").put({fbase_key:"firebase:authUser:${auth.apiKey}:[DEFAULT]",value:{uid:"${auth.uid}",email:"${auth.email}",emailVerified:false,isAnonymous:false,providerData:[{providerId:"password",uid:"${auth.email}",email:"${auth.email}"}],stsTokenManager:{refreshToken:"${auth.refreshToken}",accessToken:"",expirationTime:0},createdAt:"1630244457351",lastLoginAt:"1769574121820",apiKey:"${auth.apiKey}",appName:"[DEFAULT]"}},"firebase:authUser:${auth.apiKey}:[DEFAULT]")}catch(x){}}})();`;
}

/**
 * Create an authenticated ITC browser session.
 * @returns {{ browser, context, page }}
 */
async function createSession() {
  const auth = getFirebaseAuth();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
  });
  await context.addInitScript({ content: buildInitScript(auth) });
  const page = await context.newPage();
  return { browser, context, page };
}

/**
 * Navigate to an ITC page by name or URL path.
 */
async function navigateTo(page, target, waitMs = 6000) {
  const urlPath = KNOWN_PAGES[target] || target;
  const url = urlPath.startsWith('http') ? urlPath : BASE_URL + urlPath;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
  await new Promise(r => setTimeout(r, waitMs));

  // Check for login redirect (session expired)
  if (page.url().includes('/authentication/login')) {
    return { ok: false, expired: true, url: page.url() };
  }
  return { ok: true, expired: false, url: page.url() };
}

/**
 * Search ITC charts using the search input.
 */
async function searchCharts(page, query) {
  // Click search input and type
  const searchInput = await page.$('input#_r_e_');
  if (searchInput) {
    await searchInput.click();
    await searchInput.fill(query);
    await new Promise(r => setTimeout(r, 2000));
  }

  // Extract matching results
  return page.evaluate(() => {
    return Array.from(document.querySelectorAll('a'))
      .map(a => ({ text: a.textContent.trim(), href: a.href }))
      .filter(l => l.href.includes('/charts/') && l.text)
      .reduce((acc, l) => {
        if (!acc.find(x => x.href === l.href)) acc.push(l);
        return acc;
      }, []);
  });
}

/**
 * Extract page content — text data visible on the page.
 */
async function extractContent(page) {
  return page.evaluate(() => ({
    url: window.location.href,
    title: document.title,
    text: document.body?.innerText?.substring(0, 5000) || '',
    links: Array.from(document.querySelectorAll('a'))
      .map(a => ({ text: a.textContent.trim().substring(0, 100), href: a.href }))
      .filter(l => l.text && l.href.includes('intothecryptoverse'))
      .reduce((acc, l) => { if (!acc.find(x => x.href === l.href)) acc.push(l); return acc; }, [])
      .slice(0, 50),
  }));
}

/**
 * Take a screenshot of the current page.
 */
async function screenshot(page, filename) {
  const outDir = path.join(__dirname, '..', 'output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, filename || `itc-${Date.now()}.png`);
  await page.screenshot({ path: outPath, fullPage: false });
  return outPath;
}

module.exports = {
  createSession, navigateTo, searchCharts, extractContent, screenshot,
  KNOWN_PAGES, BASE_URL,
};

// CLI test
if (require.main === module) {
  (async () => {
    const { browser, page } = await createSession();
    const target = process.argv[2] || 'dashboard';
    const result = await navigateTo(page, target);
    console.log('Nav:', result);
    if (result.ok) {
      const content = await extractContent(page);
      console.log('Title:', content.title);
      console.log('Text preview:', content.text.substring(0, 500));
    }
    await browser.close();
  })();
}
