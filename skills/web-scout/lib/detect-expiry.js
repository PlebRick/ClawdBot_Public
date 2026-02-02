/**
 * Session expiry detection for authenticated sites.
 * Returns true if the current page indicates an expired/logged-out session.
 */

const EXPIRY_PATTERNS = {
  itc: {
    urlPatterns: [/login/i, /signin/i, /sign-in/i],
    domSelectors: ['[class*="login-form"]', '[id*="login"]'],
  },
  logos: {
    urlPatterns: [/login/i, /signin/i, /identity/i, /auth.*redirect/i],
    domSelectors: ['[class*="login"]', '[class*="sign-in"]'],
  },
};

async function isSessionExpired(page, profile) {
  const patterns = EXPIRY_PATTERNS[profile];
  if (!patterns) return false;

  const url = page.url();

  // Check URL patterns
  for (const pattern of patterns.urlPatterns) {
    if (pattern.test(url)) return true;
  }

  // Check DOM selectors
  for (const sel of patterns.domSelectors) {
    const found = await page.$(sel).catch(() => null);
    if (found) return true;
  }

  return false;
}

module.exports = { isSessionExpired };
