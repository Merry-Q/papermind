import {chromium} from 'playwright-core';
import {writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
const base='http://127.0.0.1:8000',did='pdf-d20a33e7eb892f38';
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const report={checks:[],errors:[]};
page.on('pageerror',e=>report.errors.push(e.message));
mkdirSync('artifacts',{recursive:true});
try{
 await page.goto(`${base}/?document=${did}`);
 await page.getByRole('heading',{name:'第 55 次中国互联网络发展状况统计报告',exact:true}).waitFor();
 assert((await page.locator('.reading-section').count())>=8);
 report.checks.push('75页真实报告生成后的正文展示');
 await page.screenshot({path:'artifacts/final-report-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:'artifacts/final-report-mobile.png',fullPage:true});
 await page.route(`**/api/documents/${did}`,async route=>{
  const response=await route.fetch();const d=await response.json();
  d.nodes=[];d.status='incomplete';d.job={...d.job,status:'failed',error:'NodeBatch field required INTERNAL_SENTINEL',detail:'已完成内容保留'};
  await route.fulfill({response,json:d});
 });
 await page.reload();
 await page.getByRole('heading',{name:'讲解尚未生成',exact:true}).waitFor();
 assert(!(await page.locator('body').innerText()).includes('INTERNAL_SENTINEL'));
 await page.getByRole('button',{name:'阅读原 PDF',exact:true}).click();
 await page.locator('.pdf-page-area img').waitFor();
 report.checks.push('重放真实失败状态：简明提示、无内部字段错误、原文入口有效');
 await page.screenshot({path:'artifacts/final-failure-mobile.png',fullPage:true});
 assert.deepEqual(report.errors,[]);report.status='passed';
}catch(e){report.status='failed';report.errors.push(e.message);throw e;}
finally{writeFileSync('artifacts/fixed-ui-report.json',JSON.stringify(report,null,2));await browser.close();}
console.log(JSON.stringify(report,null,2));
