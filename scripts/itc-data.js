#!/usr/bin/env node
/**
 * ITC (IntoTheCryptoverse) Data Fetcher
 * Fetches key macro/risk metrics for weekly market report
 * 
 * Usage: node itc-data.js
 * Output: JSON with risk levels, recession data, macro indicators
 */

const { createSession, navigateTo, extractContent } = require('../skills/web-scout/profiles/itc.js');

async function fetchRiskLevel(page, asset) {
  const navResult = await navigateTo(page, `${asset}-risk`, 4000);
  if (!navResult.ok || navResult.expired) {
    return { asset, ok: false, expired: navResult.expired };
  }
  
  const content = await extractContent(page);
  const text = content.text;
  
  // Parse risk level from page text
  // Look for patterns like "Risk Level: 0.45" or "0.45"
  const riskMatch = text.match(/(?:risk|level)[:\s]*([0-9.]+)/i) 
    || text.match(/([0-9.]{3,5})/);
  
  return {
    asset,
    ok: true,
    url: content.url,
    title: content.title,
    textPreview: text.substring(0, 300),
    riskValue: riskMatch ? parseFloat(riskMatch[1]) : null
  };
}

async function fetchMacroPage(page, pageName, waitMs = 5000) {
  const navResult = await navigateTo(page, pageName, waitMs);
  if (!navResult.ok || navResult.expired) {
    return { page: pageName, ok: false, expired: navResult.expired };
  }
  
  const content = await extractContent(page);
  return {
    page: pageName,
    ok: true,
    url: content.url,
    title: content.title,
    textPreview: content.text.substring(0, 500)
  };
}

async function main() {
  let browser;
  const output = {
    source: 'itc',
    timestamp: new Date().toISOString(),
    ok: true,
    sessionExpired: false,
    data: {}
  };
  
  try {
    const session = await createSession();
    browser = session.browser;
    const page = session.page;
    
    // Check session validity with dashboard first
    const dashCheck = await navigateTo(page, 'dashboard', 3000);
    if (dashCheck.expired) {
      output.ok = false;
      output.sessionExpired = true;
      output.error = 'ITC Firebase session expired - re-login required';
      console.log(JSON.stringify(output, null, 2));
      await browser.close();
      return;
    }
    
    // Fetch BTC risk
    output.data.btcRisk = await fetchRiskLevel(page, 'btc');
    
    // Fetch recession / interest rate data
    output.data.macro = await fetchMacroPage(page, 'interest-rate', 5000);
    
    // Fetch MVRV-Z score
    output.data.mvrvZ = await fetchMacroPage(page, 'mvrv-z', 4000);
    
    // Fetch Fear & Greed (ITC's version)
    output.data.fearGreed = await fetchMacroPage(page, 'fear-greed', 4000);
    
    console.log(JSON.stringify(output, null, 2));
    
  } catch (err) {
    output.ok = false;
    output.error = err.message;
    console.log(JSON.stringify(output, null, 2));
  } finally {
    if (browser) await browser.close();
  }
}

main();
