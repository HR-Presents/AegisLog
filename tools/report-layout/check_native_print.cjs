const {chromium} = require('playwright');
const {pathToFileURL} = require('url');
const path = require('path');
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  await page.goto(pathToFileURL(path.resolve('report-layout-qa/native-print/windows-System-1440min-aegislog-report.html')).href);
  await page.evaluate(async () => {await document.fonts.ready; await Promise.all([...document.images].map(img => img.decode()));});
  if (await page.locator('.issue').count() !== 3) throw Error('Lost review groups');
  if (!(await page.locator('.scope-grid').innerText()).includes('Count limit reached')) throw Error('Lost native collection scope');
  await page.setViewportSize({width:390,height:844});
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw Error('Mobile overflow');
  await page.setViewportSize({width:1440,height:1000});
  await page.emulateMedia({media:'print'});
  await page.pdf({path:'report-layout-qa/native-print/summary.pdf',format:'A4',preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false});
  await browser.close();
  console.log('Native scope, three-group retention and mobile layout passed');
})().catch(error => {console.error(error);process.exit(1);});
