const { chromium } = require('playwright');

class BrowserSession {
  constructor(options = {}) {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.headless = options.headless !== false;
    this.minDelay = options.minDelay || 2000;
    this.lastNav = 0;
  }

  async launch(cookies = null) {
    this.browser = await chromium.launch({ headless: this.headless });
    this.context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      viewport: { width: 1280, height: 900 },
    });
    if (cookies && cookies.length) {
      await this.context.addCookies(cookies);
    }
    this.page = await this.context.newPage();
    return this.page;
  }

  async rateLimit() {
    const now = Date.now();
    const elapsed = now - this.lastNav;
    if (elapsed < this.minDelay) {
      await new Promise(r => setTimeout(r, this.minDelay - elapsed));
    }
    this.lastNav = Date.now();
  }

  async goto(url, options = {}) {
    await this.rateLimit();
    const response = await this.page.goto(url, {
      waitUntil: options.waitUntil || 'domcontentloaded',
      timeout: options.timeout || 30000,
    });
    return response;
  }

  async screenshot(path) {
    return this.page.screenshot({ path, fullPage: true });
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.context = null;
      this.page = null;
    }
  }
}

module.exports = { BrowserSession };
