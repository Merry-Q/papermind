import {chromium} from 'playwright-core';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
const [input,output]=process.argv.slice(2),report={checks:[],errors:[],requests:[]};
const browser=await chromium.launch({channel:'msedge',headless:true});
try{const page=await browser.newPage({viewport:{width:860,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>report.errors.push(e.message));await page.route('**/*',r=>{report.requests.push(r.request().url());r.abort();});await page.setContent(readFileSync(input,'utf8'));await page.locator('body[data-pm-ready=true]').waitFor();
await page.locator('button[data-source]').first().click();if(!await page.locator('#pm-local-source blockquote').innerText())throw Error('独立页面原句弹窗缺失');await page.locator('#pm-local-source button').click();report.checks.push('离线引用回查及关闭');
await page.locator('#overview-chain').click();if(await page.locator('#overview-edges').getAttribute('data-mode')!=='chain')throw Error('首屏结构切换失败');await page.locator('#overview-direct').click();report.checks.push('首屏关系切换');
if(await page.locator('[data-ask]:visible,[data-concept]:visible').count())throw Error('独立导出出现不能执行的宿主操作');report.checks.push('独立页隐藏宿主专用动作');
const label=await page.locator('.attn-axis-caption').innerText();if(!label.includes('0到1')||!label.includes('不是概率'))throw Error('权重/输出说明缺失');report.checks.push('权重坐标及输出区分');
const font=await page.locator('#attn-reset').evaluate(e=>getComputedStyle(e).fontSize);if(parseFloat(font)<13)throw Error('复位字号过小');report.checks.push('复位字号 '+font);
if(report.errors.length||report.requests.length)throw Error(JSON.stringify(report));report.status='pass';
}catch(e){report.status='failed';report.errors.push(e.message);}finally{await browser.close();mkdirSync(path.dirname(output),{recursive:true});writeFileSync(output,JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
