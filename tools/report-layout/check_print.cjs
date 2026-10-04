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
  const cover = page.locator('.aegis-report-header');
  if (!await cover.isVisible()) throw Error('AegisLog brief header missing');
  if (!await cover.locator('.cover-logo').isVisible()) throw Error('AegisLog logo missing');
  await cover.getByRole('link', {name:'View investigation results'}).click();
  if (!page.url().endsWith('#executive')) throw Error('Cover shortcut failed');
  const logoWidth = await cover.locator('.cover-logo').evaluate(item => item.getBoundingClientRect().width);
  if (logoWidth < 180) throw Error('Report logo is too small');
  const stops = await cover.locator('stop').evaluateAll(items => items.map(item => item.getAttribute('stop-color')));
  if (!stops.includes('#b9e6ed')) throw Error('Light sea-blue palette missing');
  const color = await cover.locator('h1').evaluate(item => getComputedStyle(item).color);
  if (color !== 'rgb(0, 0, 0)') throw Error('Header title must be black');
  if (await page.locator('.cover-cards > div').count() !== 4) throw Error('Cover metadata cards missing');
  if (await page.locator('.document-contents a').count() !== 8) throw Error('Contents missing');
  const colored = await page.locator('#aegislog-report *').evaluateAll(items => items.filter(item =>
    !item.closest('.aegis-report-header, .document-contents') && !item.classList.contains('section-label') &&
    item.textContent.trim() && !item.children.length && getComputedStyle(item).color !== 'rgb(0, 0, 0)'
  ).map(item => item.className));
  if (colored.length) throw Error(`Non-black body text: ${colored}`);
  await page.getByRole('link', {name:'Findings & Next Actions', exact:true}).click();
  if (!page.url().endsWith('#findings')) throw Error('Contents link failed');
  const disclosure = page.locator('details.report-evidence').first();
  if (await disclosure.getAttribute('open') !== null) throw Error('Evidence should start collapsed');
  await disclosure.locator('summary').click();
  if (!await disclosure.locator('.evidence').isVisible()) throw Error('Evidence did not expand');
  await disclosure.locator('summary').click();
  await page.goto('about:blank');
  await page.goto(pathToFileURL(path.resolve('report-layout-qa/demo_auth-aegislog-report.html')).href);
  await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(img => img.decode())); });
  await page.screenshot({path:'report-layout-qa/summary-desktop.png'});
  await page.setViewportSize({width:390,height:844});
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw Error('Summary overflows mobile screen');
  const titleWidth = await page.locator('.summary-finding .record-head strong').first().evaluate(item => item.getBoundingClientRect().width);
  if (titleWidth < 200) throw Error('Mobile finding title is unnecessarily narrow');
  await page.screenshot({path:'report-layout-qa/summary-mobile.png',fullPage:true});
  await page.setViewportSize({width:1440,height:900});
  await page.emulateMedia({media:'print'});
  if (await page.locator('.cover-results').isVisible()) throw Error('Screen shortcut leaked into print');
  await page.pdf({path:'report-layout-qa/demo-summary.pdf',format:'A4',printBackground:true,displayHeaderFooter:false});
  await page.emulateMedia({media:'screen'});
  await page.getByRole('link',{name:'Print complete report / Save PDF'}).click();
  if (!page.url().includes('-appendix.html?print=1')) throw Error('Complete print action failed');
  await page.waitForLoadState('load');
  await page.getByRole('heading', {name:'Security Investigation Report', exact:true}).waitFor({state:'visible'});
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.decode()));
  });
  await page.screenshot({path:'report-layout-qa/complete-desktop.png'});
  await page.setViewportSize({width:390,height:844});
  if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw Error('Full report overflows mobile screen');
  await page.setViewportSize({width:1440,height:900});
  await page.emulateMedia({media:'print'});
  await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
  if (!await page.locator('.evidence-group').first().isVisible()) throw Error('Printed evidence group identifier missing');
  await page.pdf({path:'report-layout-qa/demo-complete.pdf',format:'A4',printBackground:true,displayHeaderFooter:false});
  const bars = await page.locator('.distribution-track i').evaluateAll(items => items.map(item => getComputedStyle(item).borderTopWidth));
  if (!bars.length || bars.some(width => width !== '7px')) throw Error('Foreground bars missing');
  await page.pdf({path:'report-layout-qa/demo-complete-no-background.pdf',format:'A4',printBackground:false,displayHeaderFooter:false});
  for (const name of ['empty', 'missing-time', 'many-findings', 'windows-context', 'wer-application']) {
    await page.emulateMedia({media:'screen'});
    await page.goto(pathToFileURL(path.resolve(`report-layout-qa/${name}-aegislog-report.html`)).href);
    await page.setViewportSize({width:390,height:844});
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)) throw Error(`${name} overflows`);
    await page.setViewportSize({width:1440,height:900});
    if (name === 'windows-context' || name === 'wer-application') await page.screenshot({path:`report-layout-qa/${name}-desktop.png`,fullPage:true});
    await page.emulateMedia({media:'print'});
    if (await page.locator('.toolbar').isVisible()) throw Error(`${name} browser controls leaked into print`);
    await page.pdf({path:`report-layout-qa/${name}.pdf`,format:'A4',printBackground:true,displayHeaderFooter:false});
  }
  await browser.close();
  console.log('Chromium filter and 161-source print smoke passed');
})().catch(error => {console.error(error);process.exit(1);});


