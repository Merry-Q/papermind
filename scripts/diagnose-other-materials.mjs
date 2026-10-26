import {chromium} from 'playwright-core';
import {readFileSync,writeFileSync} from 'node:fs';
const cases=JSON.parse(readFileSync('artifacts/reading-v2/other-materials/diagnostic-input.json','utf8'));
const browser=await chromium.launch({channel:'msedge',headless:true});const results=[];
for(const c of cases){
 const p=await browser.newPage({viewport:{width:1000,height:1000}}),errors=[];
 p.on('pageerror',e=>errors.push({message:e.message,stack:e.stack}));
 const html=readFileSync(c.file,'utf8');
 await p.setContent('<iframe sandbox="allow-scripts" style="width:100%;height:1000px;border:0"></iframe>');
 await p.locator('iframe').evaluate((e,h)=>e.srcdoc=h,html);
 await p.waitForTimeout(700);
 const f=p.frameLocator('iframe');const status=await f.locator('body').evaluate(e=>({ready:e.dataset.pmReady,error:e.dataset.pmError}));
 for(const e of errors){const line=Number(e.stack.match(/about:srcdoc:(\d+):/)?.[1]);if(line)e.context=html.split('\n').slice(Math.max(0,line-5),line+3).join('\n');}
 results.push({...c,...status,errors});await p.close();
}
await browser.close();writeFileSync('artifacts/reading-v2/other-materials/initialization-diagnosis.json',JSON.stringify(results,null,2));
console.log(JSON.stringify(results.filter(v=>v.errors.length||!v.ready),null,2));
