const fs = require('fs');
const path = require('path');
const { BrowserSession } = require('./session');
const { isSessionExpired } = require('./detect-expiry');

const COOKIES_DIR = path.join(__dirname, '..', 'cookies');

/**
 * Create an authenticated browser session for a given profile.
 * @param {string} profile - 'itc', 'logos', or 'cnn' (no auth)
 * @returns {{ session: BrowserSession, page: Page }}
 */
async function openProfile(profile) {
  let cookies = null;
  const cookieFile = path.join(COOKIES_DIR, `${profile}-cookies.json`);

  if (fs.existsSync(cookieFile)) {
    cookies = JSON.parse(fs.readFileSync(cookieFile, 'utf8'));
  }

  const session = new BrowserSession();
  await session.launch(cookies);
  return session;
}

/**
 * Navigate to a URL with auth, expiry detection, and backoff.
 * @param {BrowserSession} session
 * @param {string} url
 * @param {string} profile - for expiry detection patterns
 * @param {object} options
 * @returns {{ ok: boolean, expired: boolean, error: string|null }}
 */
async function navigateTo(session, url, profile, options = {}) {
  const maxRetries = options.retries || 3;
  let delay = 2000;

  for (let i = 0; i < maxRetries; i++) {
    try {
      await session.goto(url, options);

      if (await isSessionExpired(session.page, profile)) {
        return {
          ok: false,
          expired: true,
          error: `Session expired for ${profile} — Rick needs to re-login on Chrome`,
        };
      }

      return { ok: true, expired: false, error: null };
    } catch (err) {
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, delay));
        delay = Math.min(delay * 2, 60000);
      } else {
        return { ok: false, expired: false, error: err.message };
      }
    }
  }
}

/**
 * Extract text content from the page using a selector.
 */
async function extractText(page, selector) {
  const el = await page.$(selector);
  if (!el) return null;
  return el.textContent();
}

/**
 * Extract all matching elements' text.
 */
async function extractAllText(page, selector) {
  return page.$$eval(selector, els => els.map(e => e.textContent.trim()));
}

/**
 * Take a screenshot and return the file path.
 */
async function captureScreenshot(session, filename) {
  const outDir = path.join(__dirname, '..', 'output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, filename);
  await session.screenshot(outPath);
  return outPath;
}

module.exports = { openProfile, navigateTo, extractText, extractAllText, captureScreenshot };
