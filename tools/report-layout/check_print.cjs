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
  await page.goto(pathToFileURL(path.resolve('report-layout-qa/demo_auth-aegislog-report.html')).href);
  await page.emulateMedia({media:'screen'});
  if (!await page.getByText('SYNTHETIC DEMO DATA', {exact:true}).isVisible()) throw Error('Demo label missing');
  await page.setViewportSize({width:1440,height:900});
  await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(img => img.decode())); });
  const cover = page.locator('.company-header');
  if (!await cover.isVisible()) throw Error('AegisLog brief header missing');
  const logoWidth = await cover.locator('img').evaluate(item => item.getBoundingClientRect().width);
  if (logoWidth < 250) throw Error('Report logo is too small');
  const color = await cover.locator('h1').evaluate(item => getComputedStyle(item).color);
  if (color !== 'rgb(0, 0, 0)') throw Error('Header title must be black');
  if (!await page.getByText('MADE BY HR-PRESENTS', {exact:true}).isVisible()) throw Error('Closing maker signature missing');
  if (await page.locator('.metric-strip > div').count() !== 4) throw Error('Metrics missing');
  const colored = await page.locator('.company-report *').evaluateAll(items => items.filter(item =>
    item.textContent.trim() && !item.children.length && getComputedStyle(item).color !== 'rgb(0, 0, 0)'
  ).map(item => item.className));
  if (colored.length) throw Error(`Non-black body text: ${colored}`);
  const evidenceLink = page.locator('.issue a[href*="#finding-"]').first();
  if (!(await evidenceLink.getAttribute('href')).includes('-appendix.html#finding-')) throw Error('Evidence reference missing');
  await page.goto('about:blank');
  await page.goto(pathToFileURL(path.resolve('report-layout-qa/demo_auth-aegislog-report.html')).href);
  await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(img => img.decode())); });
  await page.screenshot({path:'report-layout-qa/summary-desktop.png'});
  await page.setViewportSize({width:390,height:844});
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw Error('Summary overflows mobile screen');
  const titleWidth = await page.locator('.issue-heading h3').first().evaluate(item => item.getBoundingClientRect().width);
  if (titleWidth < 200) throw Error('Mobile finding title is unnecessarily narrow');
  await page.screenshot({path:'report-layout-qa/summary-mobile.png',fullPage:true});
  await page.setViewportSize({width:1440,height:900});
  await page.emulateMedia({media:'print'});
  if (await page.locator('.screen-tools').isVisible()) throw Error('Screen shortcut leaked into print');
  await page.pdf({path:'report-layout-qa/demo-summary.pdf',format:'A4',printBackground:true,displayHeaderFooter:false});
  await page.emulateMedia({media:'screen'});
  await page.getByRole('link',{name:'Print complete report / Save PDF'}).click();
  if (!page.url().includes('-appendix.html?print=1')) throw Error('Complete print action failed');
  await page.waitForLoadState('load');
  await page.getByRole('heading', {name:'Investigation report', exact:true}).waitFor({state:'visible'});
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.decode()));
  });
  await page.screenshot({path:'report-layout-qa/complete-desktop.png'});
  async function verifyTelemetryRow() {
    const bounds = await page.locator('.supporting .chart').evaluateAll(cards =>
      cards.map(card => {const box = card.getBoundingClientRect(); return {x:box.x,y:box.y,right:box.right};}));
    if (bounds.length !== 3 || bounds.some(box => Math.abs(box.y - bounds[0].y) > 1)
        || bounds[0].right > bounds[1].x || bounds[1].right > bounds[2].x) {
      throw Error('Categories, log levels and services must align side by side');
    }
  }
  await page.locator('.supporting').evaluate(item => item.open = true);
  await verifyTelemetryRow();
  await page.locator('.supporting').screenshot({path:'report-layout-qa/telemetry-desktop.png'});
  await page.setViewportSize({width:390,height:844});
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw Error('Full report overflows mobile screen');
  await page.setViewportSize({width:1440,height:900});
  await page.emulateMedia({media:'print'});
  await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
  if (await page.locator('.supporting').isVisible()) throw Error('Browser-only context leaked into compact print');
  if (!await page.locator('.excerpt').first().isVisible()) throw Error('Printed retained evidence missing');
  await page.pdf({path:'report-layout-qa/demo-complete.pdf',format:'A4',printBackground:true,displayHeaderFooter:false});
  await page.pdf({path:'report-layout-qa/demo-complete-no-background.pdf',format:'A4',printBackground:false,displayHeaderFooter:false});
  for (const name of ['empty', 'missing-time', 'many-findings', 'windows-context', 'wer-application']) {
    await page.emulateMedia({media:'screen'});
    await page.goto(pathToFileURL(path.resolve(`report-layout-qa/${name}-aegislog-report.html`)).href);
    await page.setViewportSize({width:390,height:844});
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw Error(`${name} overflows`);
    await page.setViewportSize({width:1440,height:900});
    if (name === 'windows-context' || name === 'wer-application') await page.screenshot({path:`report-layout-qa/${name}-desktop.png`,fullPage:true});
    await page.emulateMedia({media:'print'});
    if (name === 'windows-context') {
      const sourceBars = await page.locator('.provider-bar i').evaluateAll(items => items.map(item => getComputedStyle(item).borderTopWidth));
      if (!sourceBars.length || sourceBars.some(width => width !== '5px')) throw Error('Timestamped source foreground bars missing');
    }
    if (await page.locator('.screen-tools').isVisible()) throw Error(`${name} browser controls leaked into print`);
    await page.pdf({path:`report-layout-qa/${name}.pdf`,format:'A4',printBackground:true,displayHeaderFooter:false});
  }
  await browser.close();
  console.log('Chromium filter and 161-source print smoke passed');
})().catch(error => {console.error(error);process.exit(1);});
