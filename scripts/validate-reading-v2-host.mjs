import {chromium} from 'playwright-core';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
const [edition,out,flag]=process.argv.slice(2);mkdirSync(out,{recursive:true});
const did='pdf-bdfaa68d8984f0dc',url=`http://127.0.0.1:8000/?document=${did}&readingV2=${edition}${flag==='inspection'?'&readingInspection=1':''}`;
const report={url,checks:[],issues:[],errors:[],mutations:[]};
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1600,height:1050},reducedMotion:'reduce'});
const page=await context.newPage();page.setDefaultTimeout(8000);
page.on('pageerror',e=>report.errors.push(e.message));
page.on('request',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.method()))report.mutations.push({method:r.method(),url:r.url()});});
const require=(c,s)=>{if(!c)throw Error(s);};
async function check(name,fn){try{report.checks.push({name,status:'pass',value:await fn()});}catch(e){report.issues.push({name,detail:e.message});report.checks.push({name,status:'fail'});}}
try{
 await page.goto(url);const frame=page.frameLocator('iframe[title="论文交互讲解"]');
 await frame.locator('body[data-pm-ready="true"]').waitFor({timeout:30000});
 await check('宿主主阅读区加载',async()=>{require(await page.locator('.rightbar').count()===1,'原右侧栏缺失');require(await page.locator('.reading-v2').count()===1,'预览未启用');await page.screenshot({path:path.join(out,'host-desktop.png')});return await page.locator('.reading-v2 iframe').getAttribute('sandbox');});
 await check('目录导航与阅读位置',async()=>{await page.locator('.outline button').filter({hasText:'缩放点积'}).click();await page.waitForFunction(()=>document.querySelector('.reading-scroll').scrollTop>500);return await page.locator('.reading-scroll').evaluate(e=>e.scrollTop);});
 await check('原文引用与返回',async()=>{await frame.locator('#scaled-dot-product button[data-source]').first().click();const source=page.locator('.source-entry');await source.waitFor();require((await source.locator('blockquote').innerText()).length>15,'来源原句未显示');const scroll=await page.locator('.reading-scroll').evaluate(e=>e.scrollTop);await source.getByRole('button',{name:/查看 PDF/}).click();await page.locator('.pdf-page-area img').waitFor();await page.getByRole('button',{name:'返回原阅读位置',exact:true}).click();await page.frameLocator('iframe[title="论文交互讲解"]').locator('body[data-pm-ready="true"]').waitFor();const after=await page.locator('.reading-scroll').evaluate(e=>e.scrollTop);require(Math.abs(after-scroll)<120,'从PDF返回丢失阅读位置');return {before:scroll,after};});
 await check('概念入口仍进入原右栏',async()=>{if(await frame.locator('button[data-concept]').count()){await frame.locator('button[data-concept]').first().click();await page.locator('.concept-title').waitFor();return await page.locator('.concept-title').innerText();}await page.getByRole('button',{name:'知识补充',exact:true}).click();require(await page.locator('.concept-row').count()>0,'右侧原概念入口缺失');return '原右栏概念入口可用';});
 await check('场景问题带入Copilot',async()=>{const button=frame.locator('button[data-ask]').first();const text=await button.getAttribute('data-ask');await button.click();await page.locator('.chat-context').waitFor();const textarea=page.locator('.rightbar textarea');require(await textarea.inputValue()===text,'场景问题未进入输入框');return {question:text,context:await page.locator('.chat-context').innerText()};});
 await check('移动端阅读和侧栏',async()=>{await page.setViewportSize({width:390,height:844});await page.locator('.reading-scroll').evaluate(e=>e.scrollTop=0);const size=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));require(size.scrollWidth<=size.width+1,'宿主横向溢出');await page.screenshot({path:path.join(out,'host-mobile.png')});await page.getByRole('button',{name:'打开 Copilot 与知识补充',exact:true}).click();require(await page.locator('.rightbar.is-open').count()===1,'移动侧栏未打开');return size;});
 await check('恢复原讲解',async()=>{await page.setViewportSize({width:1600,height:1050});await page.getByRole('button',{name:'恢复原讲解',exact:true}).click();await page.locator('.reading-article').waitFor();require(await page.locator('.reading-section').count()===10,'原讲解节点未恢复');});
 await check('预览无业务写入',async()=>{require(report.mutations.length===0,JSON.stringify(report.mutations));require(report.errors.length===0,JSON.stringify(report.errors));});
}catch(e){report.issues.push({name:'initialization',detail:e.message});}
finally{report.status=report.issues.length?'failed':'pass';writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report,null,2));}
