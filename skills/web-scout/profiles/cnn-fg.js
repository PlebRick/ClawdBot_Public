const { BrowserSession } = require('../lib/session');

const CNN_FG_URL = 'https://www.cnn.com/markets/fear-and-greed';

async function fetchFearAndGreed() {
  const session = new BrowserSession();
  try {
    await session.launch();
    await session.goto(CNN_FG_URL, { waitUntil: 'networkidle' });

    await session.page.waitForSelector('.market-fng-gauge__dial-number-value', { timeout: 15000 }).catch(() => null);

    const data = await session.page.evaluate(() => {
      const result = {
        source: 'cnn-fear-greed',
        timestamp: new Date().toISOString(),
        data: { index: null, label: null, components: {} }
      };

      // Main index value
      const dialVal = document.querySelector('.market-fng-gauge__dial-number-value');
      if (dialVal) result.data.index = parseInt(dialVal.textContent.trim(), 10);

      // Label from meter data attribute or label element
      const meter = document.querySelector('.market-fng-gauge__meter[data-index-label]');
      if (meter) {
        result.data.label = meter.getAttribute('data-index-label');
      } else {
        const labelEl = document.querySelector('.market-fng-gauge__label');
        if (labelEl) result.data.label = labelEl.textContent.trim();
      }

      // Components — each .market-fng-indicator has name + value-label
      const indicators = document.querySelectorAll('.market-fng-indicator');
      indicators.forEach(el => {
        const nameEl = el.querySelector('.market-fng-indicator__name');
        const valueEl = el.querySelector('.market-fng-indicator__value-label');
        if (nameEl && valueEl) {
          const name = nameEl.textContent.trim().toLowerCase().replace(/\s+/g, '_');
          const label = valueEl.textContent.trim().toLowerCase();
          if (name) result.data.components[name] = label;
        }
      });

      return result;
    });

    return data;
  } finally {
    await session.close();
  }
}

if (require.main === module) {
  fetchFearAndGreed()
    .then(data => console.log(JSON.stringify(data, null, 2)))
    .catch(err => {
      console.error('Error:', err.message);
      process.exit(1);
    });
}

module.exports = { fetchFearAndGreed };
