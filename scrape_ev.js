const { chromium } = require('playwright');

async function fetchEVData() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.setDefaultTimeout(60000);

  console.log('Fetching EV data from CEM...');
  await page.goto('https://ev.cem-macau.com/zh/WhereToCharge', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(10000);

  const client = await page.context().newCDPSession(page);
  
  const result = await client.send('Runtime.evaluate', {
    expression: `
      JSON.stringify(data.list.map(s => {
        const availablePiles = s.pilerecords ? s.pilerecords.filter(p => p.status === 0).length : 0;
        const totalPiles = s.pilerecords ? s.pilerecords.length : 0;
        let name = s.stationname.replace(/停車場$/, '').trim();
        return { name: name, available: availablePiles, total: totalPiles };
      }))
    `,
    returnByValue: true
  });
  
  console.log(result.result.value);

  await browser.close();
}

fetchEVData().catch(console.error);