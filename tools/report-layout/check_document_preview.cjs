const {chromium} = require('playwright');
const {pathToFileURL} = require('url');
const path = require('path');
const root = 'report-layout-qa/document-preview';
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  await page.goto(pathToFileURL(path.resolve(root, 'AegisLog-Document-Report-Preview.html')).href);
  await page.evaluate(() => document.fonts.ready);
  if (await page.locator('.excerpt').count() !== 4) throw Error('Retained evidence missing');
  if (await page.locator('.finding-register tbody tr').count() !== 3) throw Error('Review groups missing');
  const broken = await page.locator('a[href^="#"]').evaluateAll(links => links.filter(a => !document.getElementById(a.getAttribute('href').slice(1))).map(a => a.getAttribute('href')));
  if (broken.length) throw Error('Broken evidence links: ' + broken.join(', '));
  for (const selector of ['h1', 'h2', '.summary p', '.excerpt pre']) {
    const colors = await page.locator(selector).evaluateAll(items => items.map(item => getComputedStyle(item).color));
    if (colors.some(color => color !== 'rgb(0, 0, 0)')) throw Error('Text must be black');
  }
  const bounds = await page.locator('.chart').evaluateAll(items => items.map(item => item.getBoundingClientRect().y));
  if (bounds.some(y => Math.abs(y-bounds[0]) > 1)) throw Error('Chart panels must align');
  await page.locator('#overview').screenshot({path:path.join(root,'desktop-overview.png')});
  await page.locator('#activity').screenshot({path:path.join(root,'desktop-activity.png')});
  await page.setViewportSize({width:390,height:844});
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth+1)) throw Error('Mobile overflow');
  await page.screenshot({path:path.join(root,'mobile-overview.png')});
  await page.setViewportSize({width:1440,height:1100});
  await page.emulateMedia({media:'print'});
  if (await page.locator('.reader-tools').isVisible()) throw Error('Browser controls in print');
  await page.pdf({path:path.join(root,'AegisLog-Document-Report-Preview.pdf'),format:'A4',printBackground:true,displayHeaderFooter:false});
  await browser.close();
  console.log('Document sample: desktop, mobile, black text, aligned charts and evidence references passed.');
})().catch(error => {console.error(error);process.exit(1);});
