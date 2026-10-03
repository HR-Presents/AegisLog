const {chromium} = require('playwright');
const {pathToFileURL} = require('url');
const path = require('path');
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  await page.goto(pathToFileURL(path.resolve('report-layout-qa/batch-index.html')).href);
  await page.screenshot({path:'report-layout-qa/browser.png'});
  await page.locator('#filter').fill('duplicate-copy');
  const matches = await page.locator('.screen-only tbody tr:visible').count();
  if (matches !== 16) throw Error(`Expected 16 duplicate search results, got ${matches}`);
  // Print must preserve the entire appendix even with an active browser filter.
  await page.emulateMedia({media:'print'});
  if (await page.locator('.screen-only').first().isVisible()) throw Error('Browser controls leaked into print');
  if (await page.locator('.print-only tbody tr:visible').count() !== 161) throw Error('Print lost selected sources');
  await page.pdf({path:'report-layout-qa/folder-overview.pdf',format:'A4',preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false});
  await browser.close();
  console.log('Chromium filter and 161-source print smoke passed');
})().catch(error => {console.error(error);process.exit(1);});
