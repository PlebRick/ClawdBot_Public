#!/usr/bin/env node
/**
 * RCL Lookup: Given a date, returns the liturgical Sunday name, year, and readings.
 * Uses `lectionary` npm for Sunday identification and lectionarypage.net for readings.
 * 
 * Usage: node rcl-lookup.js YYYY-MM-DD
 * Output: JSON with sundayName, year, readings[]
 */

const https = require('https');
const http = require('http');

// Map lectionary shortName to lectionarypage.net URL slug
function mapToUrl(shortName, year) {
  const letter = year; // A, B, or C
  
  // Normalize the short name
  const name = shortName.trim();
  
  // Build slug mapping
  const seasonMap = {
    'Advent': { folder: 'Advent', prefix: 'Adv' },
    'Christmas': { folder: 'Christmas', prefix: 'Christmas' },
    'Epiphany': { folder: 'Epiphany', prefix: 'Epi' },
    'Lent': { folder: 'Lent', prefix: 'Lent' },
    'Easter': { folder: 'Easter', prefix: 'Easter' },
    'Pentecost': { folder: 'Pentecost', prefix: 'Pent' },
  };
  
  // Special cases
  const specialMap = {
    'Ash Wednesday': { path: 'YearABC/Lent/AshWed.html', shared: true },
    'Palm Sunday': { folder: 'HolyWeek', slug: `${letter}Palm_RCL` },
    'Maundy Thursday': { path: 'YearABC/HolyWeek/MaundyThurs.html', shared: true },
    'Good Friday': { path: 'YearABC/HolyWeek/GoodFri.html', shared: true },
    'Easter Vigil': { folder: 'Easter', slug: `${letter}EasVigil_RCL` },
    'Easter Day': { folder: 'Easter', slug: `${letter}EasterPrin_RCL` },
    'Trinity Sunday': { folder: 'Pentecost', slug: `${letter}Trinity_RCL` },
    'Christ the King': { folder: 'Pentecost', slug: `${letter}Proper29_RCL` },
    'Reign of Christ': { folder: 'Pentecost', slug: `${letter}Proper29_RCL` },
    'Transfiguration': { folder: 'Epiphany', slug: `${letter}EpiLast_RCL` },
    'Last Epiphany': { folder: 'Epiphany', slug: `${letter}EpiLast_RCL` },
  };
  
  // Check special cases first
  for (const [key, val] of Object.entries(specialMap)) {
    if (name.toLowerCase().includes(key.toLowerCase())) {
      if (val.shared) return val.path;
      return `Year${letter}_RCL/${val.folder}/${val.slug}.html`;
    }
  }
  
  // Parse "Season N" pattern
  const match = name.match(/^(Advent|Christmas|Epiphany|Lent|Easter|Pentecost)\s+(\d+)$/i);
  if (match) {
    const season = match[1];
    const num = match[2];
    const info = seasonMap[season];
    if (info) {
      const slug = `${letter}${info.prefix}${num}_RCL`;
      return `Year${letter}_RCL/${info.folder}/${slug}.html`;
    }
  }
  
  // Parse "Proper N" pattern (Pentecost season)
  const properMatch = name.match(/Proper\s+(\d+)/i);
  if (properMatch) {
    const num = parseInt(properMatch[1]);
    // lectionarypage.net uses "Prop" not "Proper", and case varies
    // Prop5-7 uppercase, prop8+ often lowercase - try both
    return `Year${letter}_RCL/Pentecost/${letter}Prop${num}_RCL.html`;
  }
  
  return null;
}

function fetch(url) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    protocol.get(url, { headers: { 'User-Agent': 'ClawdBot-Liturgy/1.0' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetch(res.headers.location).then(resolve).catch(reject);
      }
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

async function getReadings(urlPath) {
  const fullUrl = `https://www.lectionarypage.net/${urlPath}`;
  const html = await fetch(fullUrl);
  
  // Extract readings from lessonCitation class
  const readings = [];
  const citationRegex = /class="lessonCitation">([^<]+)/g;
  let match;
  while ((match = citationRegex.exec(html)) !== null) {
    readings.push(match[1].trim());
  }
  
  // Categorize readings
  const result = { ot: null, psalm: null, nt: null, gospel: null };
  for (const r of readings) {
    if (/psalm/i.test(r)) {
      result.psalm = r;
    } else if (/^(?:matthew|mark|luke|john)\b/i.test(r) && !/^\d\s*(john)/i.test(r)) {
      result.gospel = r;
    } else if (/^acts\b/i.test(r)) {
      // Acts replaces OT reading in Easter season
      if (!result.ot) result.ot = r;
      else result.nt = r;
    } else if (/romans|corinthians|galatians|ephesians|philippians|colossians|thessalonians|timothy|titus|philemon|hebrews|james|peter|jude|revelation/i.test(r) || /^\d\s*john/i.test(r)) {
      result.nt = r;
    } else {
      result.ot = r;
    }
  }
  
  return result;
}

async function main() {
  const dateStr = process.argv[2];
  if (!dateStr) {
    console.error('Usage: node rcl-lookup.js YYYY-MM-DD');
    process.exit(1);
  }
  
  // Use lectionary npm package
  let lectionary;
  try {
    lectionary = require('lectionary');
  } catch (e) {
    console.error('Install lectionary: npm install lectionary');
    process.exit(1);
  }
  
  const [year, month, day] = dateStr.split('-').map(Number);
  const targetDate = new Date(year, month - 1, day);
  
  // Get all Sundays for that month
  const sundays = lectionary(year, month - 1); // 0-indexed month
  
  // Find matching Sunday
  let found = null;
  for (const s of sundays) {
    const sDate = new Date(s.date);
    if (sDate.getFullYear() === year && sDate.getMonth() === month - 1 && sDate.getDate() === day) {
      found = s;
      break;
    }
  }
  
  if (!found) {
    // Try adjacent months (edge case)
    for (const m of [month - 2, month]) {
      const alt = lectionary(year, m);
      for (const s of alt) {
        const sDate = new Date(s.date);
        if (sDate.getFullYear() === year && sDate.getMonth() === month - 1 && sDate.getDate() === day) {
          found = s;
          break;
        }
      }
      if (found) break;
    }
  }
  
  if (!found) {
    console.log(JSON.stringify({ error: `No liturgical Sunday found for ${dateStr}` }));
    process.exit(1);
  }
  
  const urlPath = mapToUrl(found.lectionaryShortName, found.lectionaryYear);
  
  const output = {
    date: dateStr,
    sundayName: found.lectionaryLongName,
    shortName: found.lectionaryShortName,
    year: found.lectionaryYear,
    readings: null,
    url: urlPath ? `https://www.lectionarypage.net/${urlPath}` : null
  };
  
  if (urlPath) {
    try {
      output.readings = await getReadings(urlPath);
    } catch (e) {
      output.readingsError = e.message;
    }
  } else {
    output.readingsError = `Could not map "${found.lectionaryShortName}" to URL`;
  }
  
  console.log(JSON.stringify(output, null, 2));
}

main().catch(e => {
  console.error(e.message);
  process.exit(1);
});
