/* Cross-paper first-pass probes. Evidence of change is not proof of correctness. */
import {chromium} from 'playwright-core';
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const [input,out,hostURL]=process.argv.slice(2);
mkdirSync(out,{recursive:true});
const report={checks:[],issues:[],errors:[],requests:[],controls:[],chapters:[],screenshots:[],host:{checks:[],issues:[],errors:[],mutations:[]}};
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1000,height:1000},reducedMotion:'reduce'});
page.setDefaultTimeout(6000);
page.on('pageerror',e=>report.errors.push(e.message));
await page.route('**/*',r=>{report.requests.push(r.request().url());r.abort();});
const require=(v,m)=>{if(!v)throw Error(m);};
async function check(name,fn,target=report){try{target.checks.push({name,status:'pass',value:await fn()});}catch(e){target.checks.push({name,status:'fail'});target.issues.push({name,detail:e.message});}}
const hash=v=>createHash('sha256').update(JSON.stringify(v)).digest('hex');
let f;
async function snapshot(chapter){return f.locator('#'+chapter).evaluate(root=>{
 const visible=e=>!!(e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none');
 const graphics=[...root.querySelectorAll('svg,canvas')].map(e=>{if(e.tagName.toLowerCase()==='canvas'){try{return {id:e.id,pixels:e.toDataURL(),visible:visible(e)};}catch{return {id:e.id,canvasError:true};}}return {id:e.id,markup:e.outerHTML,visible:visible(e)};});
 const tables=[...root.querySelectorAll('table')].map(e=>e.innerText);
 const outputs=[...root.querySelectorAll('output,[data-value],[data-values]')].map(e=>({id:e.id,text:e.innerText,value:e.dataset.value,values:e.dataset.values,visible:visible(e)}));
 const clone=root.cloneNode(true);clone.querySelectorAll('button,input,select,label,nav,.pm-reading-tools').forEach(e=>e.remove());
 const relations=[...root.querySelectorAll('[class],[style],[hidden]')].filter(e=>!e.matches('button,input,select,option,label')&&!e.closest('.pm-reading-tools')).map(e=>({id:e.id,tag:e.tagName,cls:e.className?.baseVal??e.className,style:e.getAttribute('style'),hidden:e.hidden,visible:visible(e)}));
 return {graphics,tables,outputs,text:clone.textContent.replace(/\s+/g,' ').trim(),relations};
});}
const changes=(a,b)=>({graphics:hash(a.graphics)!==hash(b.graphics),tables:hash(a.tables)!==hash(b.tables),outputs:hash(a.outputs)!==hash(b.outputs),relationships:hash(a.relations)!==hash(b.relations),text:a.text!==b.text});
async function shot(name,locator){try{if(locator)await locator.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,name+'.png')});report.screenshots.push(name+'.png');}catch(e){report.issues.push({name:'screenshot '+name,detail:e.message});}}
try{
 await page.setContent('<iframe title="cross-paper inspection" sandbox="allow-scripts" style="width:100%;height:1000px;border:0"></iframe>');
 await page.locator('iframe').evaluate((e,html)=>e.srcdoc=html,readFileSync(input,'utf8'));
 f=page.frameLocator('iframe');
 await check('initialization',async()=>{await f.locator('body[data-pm-ready=true]').waitFor({timeout:12000});const error=await f.locator('body').getAttribute('data-pm-error');require(!error,error);return 'ready';});
 const initialized=await f.locator('body[data-pm-ready=true]').count();
 if(initialized){
 await page.evaluate(()=>{window.pmMessages=[];addEventListener('message',e=>window.pmMessages.push(e.data));});
 await check('node coverage, visible content and source IDs',async()=>{const v=await f.locator('body').evaluate(()=>({nodes:paperMindData.nodes.map(n=>({id:n.id,exists:!!document.getElementById(n.id),text:document.getElementById(n.id)?.innerText?.length||0})),refs:[...document.querySelectorAll('[data-source]')].map(e=>e.dataset.source),known:Object.keys(paperMindData.sources)}));require(v.nodes.every(n=>n.exists&&n.text>20),'empty or missing canonical node');require(v.refs.length>0&&v.refs.every(id=>v.known.includes(id)),'missing or unknown source');return v;});
 await shot('desktop-hero');
 const chapters=await f.locator('.paper-chapter').evaluateAll(es=>es.map(e=>({id:e.id,title:e.querySelector('h2')?.textContent,controls:e.querySelectorAll('input,select,button,summary').length})));
 report.chapters=chapters;
 for(let ci=0;ci<chapters.length;ci++){
  const chapter=chapters[ci], root=f.locator('#'+chapter.id);
  await shot('chapter-'+ci,root);
  const candidates=await root.locator('input,select,button,summary,canvas,svg[data-interactive],[data-highlight],[data-target],[role="button"],[tabindex="0"]').evaluateAll(es=>es.filter(e=>!e.matches('[data-source],[data-ask],[data-concept],[data-undo]')).map((e,i)=>{const token='probe-'+i;e.setAttribute('data-pm-probe',token);return {token,tag:e.tagName,type:e.type,id:e.id,label:(e.getAttribute('aria-label')||e.labels?.[0]?.innerText||e.innerText||e.id||'').slice(0,160),value:e.value,min:e.min,max:e.max,step:e.step,disabled:e.disabled,options:e.options?[...e.options].map(o=>({value:o.value,text:o.textContent,disabled:o.disabled})):null};}));
  for(const control of candidates){
   const result={chapter:chapter.id,...control,traces:[],errors:[]};report.controls.push(result);
   const el=root.locator('[data-pm-probe="'+control.token+'"]');
   if(control.disabled||!await el.isVisible()){result.skipped='disabled or not visible';continue;}
   const original=await snapshot(chapter.id);
   const variants=control.tag==='SELECT'?control.options.filter(o=>!o.disabled).slice(0,12).map(o=>o.value):control.type==='range'||control.type==='number'?(()=>{const a=Number(control.min||0),b=Number(control.max||Math.max(10,Number(control.value)*2)),step=Number(control.step||1);return [...new Set([a,Math.round(((a+b)/2-a)/step)*step+a,b])].map(v=>String(Number(v.toFixed(8))));})():[null];
   for(const v of variants){try{
    if(['SELECT','INPUT','BUTTON'].includes(control.tag)&&await el.isDisabled()){result.traces.push({input:v,skipped:'disabled by the preceding operation'});continue;}
    const before=await snapshot(chapter.id);
    if(control.tag==='SELECT')await el.selectOption(v);
    else if(control.type==='range'||control.type==='number'){await el.fill(v);await el.dispatchEvent('input');await el.dispatchEvent('change');}
    else if(control.type==='checkbox'||control.type==='radio')await el.setChecked(control.type==='radio'?true:!await el.isChecked());
    else if(control.tag==='CANVAS')await el.click({position:{x:Math.min(80,((await el.boundingBox())?.width||100)/2),y:30}});
    else await el.click();
    await page.waitForTimeout(100);
    const after=await snapshot(chapter.id),delta=changes(before,after);
    result.traces.push({input:v,change:delta,output:after.outputs,textExcerpt:after.text!==before.text?after.text.slice(0,1600):undefined,
      geometryHash:hash(after.graphics),tables:delta.tables?after.tables:undefined});
    const refs=await root.locator('[data-source]').evaluateAll(es=>es.filter(e=>!paperMindData.sources[e.dataset.source]).map(e=>e.dataset.source));
    if(refs.length)result.errors.push('unknown dynamic source IDs '+refs.join(','));
   }catch(e){result.errors.push(e.message);}}
   result.observableChange=result.traces.some(t=>t.change&&Object.values(t.change).some(Boolean));
   result.graphicDataOrRelationChange=result.traces.some(t=>t.change&&(t.change.graphics||t.change.tables||t.change.outputs||t.change.relationships));
   if(result.observableChange&&!chapter.changeScreenshot){await shot('chapter-'+ci+'-changed',root);chapter.changeScreenshot=true;}
   // Restore inputs only; clicking arbitrary buttons again would not reliably reset state.
   try{if(control.tag==='SELECT')await el.selectOption(control.value);else if(['range','number'].includes(control.type)){await el.fill(control.value);await el.dispatchEvent('input');await el.dispatchEvent('change');}}catch{}
   if(result.errors.length)report.issues.push({name:'control '+chapter.id+' '+control.id,detail:result.errors.join(';')});
  }
  const probes=report.controls.filter(c=>c.chapter===chapter.id&&!c.skipped);
  chapter.operated=probes.length;chapter.changed=probes.filter(c=>c.observableChange).length;chapter.graphicDataOrRelationChanged=probes.filter(c=>c.graphicDataOrRelationChange).length;
  if(!chapter.graphicDataOrRelationChanged&&probes.length)report.issues.push({name:'meaningful interaction '+chapter.id,detail:'No observed graphic, output data or relationship change. Inspect text-only traces before judging educational value.'});
 }
 await check('citations bridge and opaque sandbox',async()=>{const b=f.locator('button[data-source]').first();await b.click();const messages=await page.evaluate(()=>window.pmMessages);require(messages.some(m=>m.type==='cite'&&m.id),'citation bridge did not emit known source');const access=await f.locator('body').evaluate(()=>{try{return parent.document.body.textContent;}catch{return 'blocked';}});require(access==='blocked','host DOM exposed');return messages.filter(m=>m.type==='cite').slice(-2);});
 for(const width of [736,390,320])await check('responsive '+width,async()=>{await page.setViewportSize({width,height:920});const size=await f.locator('body').evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('.paper-chapter')].filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>({id:e.id,client:e.clientWidth,scroll:e.scrollWidth}))}));if(width===390)await shot('mobile-hero',f.locator('.paper-hero'));require(size.scrollWidth<=size.viewport+2,JSON.stringify(size));return size;});
 await check('runtime errors, finite outputs and no external requests',async()=>{const text=await f.locator('body').innerText();require(!/\bNaN\b|\bInfinity\b/.test(text),'nonfinite output');require(report.errors.length===0,report.errors.join(';'));require(report.requests.length===0,'external requests');});
 }
}catch(e){report.issues.push({name:'probe infrastructure',detail:e.stack});}
// Real host integration: read-only browser, never submit a Copilot question or persist concepts.
if(hostURL){
 const host=await browser.newPage({viewport:{width:1600,height:1050},reducedMotion:'reduce'});host.setDefaultTimeout(5000);
 host.on('pageerror',e=>report.host.errors.push(e.message));
 await host.route('**/*',r=>{if(['POST','PUT','PATCH','DELETE'].includes(r.request().method())){report.host.mutations.push({method:r.request().method(),url:r.request().url()});return r.abort();}return r.continue();});
 try{
 await host.goto(hostURL);const hf=host.frameLocator('iframe[title="论文交互讲解"]');
 await check('host rendering',async()=>{await hf.locator('body[data-pm-ready=true]').waitFor({timeout:25000});require(await host.locator('.rightbar').count()===1,'rightbar missing');await host.screenshot({path:path.join(out,'host-desktop.png')});return await host.locator('.reading-v2 iframe').getAttribute('sandbox');},report.host);
 if(await hf.locator('body[data-pm-ready=true]').count()){
 await check('outline navigation',async()=>{const buttons=host.locator('.outline button');await buttons.nth(Math.max(0,(await buttons.count())-2)).click();await host.waitForFunction(()=>document.querySelector('.reading-scroll')?.scrollTop>200);return await host.locator('.reading-scroll').evaluate(e=>e.scrollTop);},report.host);
 await check('source, PDF and return position',async()=>{await hf.locator('button[data-source]').last().click();const entry=host.locator('.source-entry');await entry.waitFor();require((await entry.locator('blockquote').innerText()).length>8,'source quote absent');const before=await host.locator('.reading-scroll').evaluate(e=>e.scrollTop);await entry.getByRole('button',{name:/查看 PDF/}).click();await host.locator('.pdf-page-area img').waitFor();await host.getByRole('button',{name:'返回原阅读位置',exact:true}).click();await host.frameLocator('iframe[title="论文交互讲解"]').locator('body[data-pm-ready=true]').waitFor();const after=await host.locator('.reading-scroll').evaluate(e=>e.scrollTop);require(Math.abs(before-after)<150,JSON.stringify({before,after}));return {before,after};},report.host);
 await check('Copilot draft in rightbar',async()=>{const b=hf.locator('button[data-ask]').first();const question=await b.getAttribute('data-ask');await b.click();await host.locator('.chat-context').waitFor();require(await host.locator('.rightbar textarea').inputValue()===question,'question not copied');return {question,context:await host.locator('.chat-context').innerText()};},report.host);
 await check('concept in rightbar',async()=>{const b=hf.locator('button[data-concept]');if(!await b.count())return 'no concept entry';await b.first().click();await host.locator('.concept-title').waitFor();return await host.locator('.concept-title').innerText();},report.host);
 await check('mobile host and sidebar',async()=>{await host.setViewportSize({width:390,height:844});const size=await host.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));require(size.scroll<=size.width+1,JSON.stringify(size));await host.screenshot({path:path.join(out,'host-mobile.png')});await host.getByRole('button',{name:'打开 Copilot 与知识补充',exact:true}).click();require(await host.locator('.rightbar.is-open').count()===1,'sidebar not open');return size;},report.host);
 await check('fallback to canonical reading',async()=>{await host.setViewportSize({width:1600,height:1050});await host.getByRole('button',{name:'恢复原讲解',exact:true}).click();await host.locator('.reading-article').waitFor();return await host.locator('.reading-section').count();},report.host);
 }
 }catch(e){report.host.issues.push({name:'host initialization',detail:e.message});}
 await check('host read-only and runtime',async()=>{require(!report.host.errors.length,report.host.errors.join(';'));require(!report.host.mutations.length,JSON.stringify(report.host.mutations));},report.host);
 await host.close();
}
report.status=report.issues.length||report.host.issues.length?'issues_recorded':'probes_passed';
writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
await browser.close();
console.log(JSON.stringify({status:report.status,controls:report.controls.length,chapters:report.chapters,issues:report.issues,hostIssues:report.host.issues}));
