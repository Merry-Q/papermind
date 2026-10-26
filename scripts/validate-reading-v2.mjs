/* One complete Attention batch: record every failure before any repair. */
import {chromium} from 'playwright-core';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const [input,out]=process.argv.slice(2);mkdirSync(out,{recursive:true});
const report={status:'running',checks:[],issues:[],errors:[],requests:[],screenshots:[]};
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:920,height:1050},reducedMotion:'reduce'});
const page=await context.newPage();page.setDefaultTimeout(2500);
page.on('pageerror',e=>report.errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')report.errors.push(m.text());});
await page.route('**/*',r=>{report.requests.push(r.request().url());r.abort();});
const close=(a,b,t=1e-6)=>Math.abs(a-b)<t;
const require=(condition,detail)=>{if(!condition)throw Error(detail);};
async function check(name,fn){try{const value=await fn();report.checks.push({name,status:'pass',value});}catch(e){report.issues.push({name,detail:e.message});report.checks.push({name,status:'fail'});}}
const softmax=s=>{const m=Math.max(...s),es=s.map(v=>Math.exp(v-m)),sum=es.reduce((a,b)=>a+b,0);return es.map(v=>v/sum);};
let frame;
try{
 await page.setContent('<iframe title="V2 inspection" sandbox="allow-scripts" style="width:100%;height:1000px;border:0"></iframe>');
 await page.locator('iframe').evaluate((el,html)=>el.srcdoc=html,readFileSync(input,'utf8'));
 frame=page.frameLocator('iframe');
 await frame.locator('body[data-pm-ready="true"]').waitFor({timeout:20000});
 const values=id=>frame.locator('#'+id).getAttribute('data-values').then(JSON.parse);
 const scalar=id=>frame.locator('#'+id).getAttribute('data-value').then(Number);
 const set=async(id,val)=>{const el=frame.locator('#'+id);if(await el.evaluate(e=>e.tagName==='SELECT'))await el.selectOption(String(val));else await el.fill(String(val));};
 const bars=selector=>frame.locator(selector).evaluateAll(es=>es.map(e=>({value:e.getAttribute('data-bleu')||e.getAttribute('data-value'),height:e.getBoundingClientRect().height,width:e.getBoundingClientRect().width})));
 const shot=async(label,selector)=>{if(selector){if(!await frame.locator(selector).count()){report.issues.push({name:'screenshot '+label,detail:'缺少目标 '+selector});return;}await frame.locator(selector).scrollIntoViewIfNeeded();}const filename=label+'.png';await page.screenshot({path:path.join(out,filename)});report.screenshots.push(filename);};
 await check('默认画面与完整节点',async()=>{const result=await frame.locator('body').evaluate(()=>({anchors:window.paperMindData.nodes.map(n=>({id:n.id,present:!!document.getElementById(n.id),visible:document.getElementById(n.id)?.getBoundingClientRect().height>0})),sources:[...document.querySelectorAll('[data-source]')].length,inputs:document.querySelectorAll('input').length}));require(result.anchors.every(n=>n.present),'核心节点缺失');require(result.sources>=10,'来源入口不足');return result;});
 await shot('desktop-hero');
 await check('QK独立计算与图高',async()=>{
  const w=await values('attn-weights'),expected=softmax([3,-2,-1].map(v=>v/Math.sqrt(3)));
  require(w.length===3&&w.every((v,i)=>close(v,expected[i],.0001)),'默认权重不符独立计算：'+JSON.stringify({w,expected}));
  require(close(await scalar('attn-output'),w[0]+2*w[1]-w[2],.0001),'默认加权输出错误');
  await set('attn-q-0',3);
  const changed=await values('attn-weights'),e2=softmax([5,-2,-3].map(v=>v/Math.sqrt(3)));
  require(changed.every((v,i)=>close(v,e2[i],.0001)),'改变Q后的权重错误');
  const b=await bars('[data-weight-index]');require(b.length===3,'需要3根可观测权重柱');
  const total=b.reduce((s,b)=>s+b.height,0);require(total>70,'权重图形塌陷');
  require(b.every((v,i)=>close(v.height/total,changed[i],.035)),'条高与权重不一致');
  return {before:w,after:changed,bars:b};
 });
 await check('V只影响输出、K真实参与计算',async()=>{
  const before=await values('attn-weights'),out0=await scalar('attn-output');await set('attn-v-0',3);
  const after=await values('attn-weights'),out1=await scalar('attn-output');require(after.every((v,i)=>close(v,before[i])),'V不应改变权重');require(close(out1-out0,2*after[0],.0001),'V输出变化错误');
  await set('attn-k-0-0',-3);const afterK=await values('attn-weights');require(!close(afterK[0],after[0]),'K没有实际改变权重');return {out0,out1,afterK};
 });
 await check('掩码与复位',async()=>{await frame.locator('#attn-mask').check();const w=await values('attn-weights');require(w[2]===0&&close(w[0]+w[1],1,.0001),'掩码未排除未来位置');await frame.locator('#attn-reset').click();require(close((await values('attn-weights'))[0],softmax([3,-2,-1].map(v=>v/Math.sqrt(3)))[0],.0001),'复位没有还原全部状态');return w;});
 await check('连续输入边界与归一化',async()=>{const traces=[];for(const q of [[0,0,0],[-3,3,-3],[3,3,3]]){for(let i=0;i<3;i++)await set('attn-q-'+i,q[i]);const w=await values('attn-weights');require(w.every(Number.isFinite)&&close(w.reduce((a,b)=>a+b,0),1,.0001),'非有限值或权重和错误');traces.push({q,w});}await frame.locator('#attn-reset').click();return traces;});
 await check('多头投影、拼接与输出',async()=>{await frame.locator('#head-select').selectOption('0');const a=await values('head-weights'),ea=softmax([1,0,-1]);await frame.locator('#head-select').selectOption('1');const b=await values('head-weights'),eb=softmax([2,-2,0]);require(a.every((v,i)=>close(v,ea[i]))&&b.every((v,i)=>close(v,eb[i])),'两组投影没有产生正确的不同权重');const expected=(ea[0]+2*ea[1]-ea[2]+eb[0]+2*eb[1]-eb[2])/2;require(close(await scalar('head-output'),expected),'拼接后的输出投影不符');return {head1:a,head2:b,output:expected};});
 await shot('desktop-attention','#scaled-dot-product');
 await check('位置编码独立计算与Canvas绘制',async()=>{await set('pe-pos',12);await set('pe-dim',7);const expected=Math.cos(12/10000**(6/64)),actual=await scalar('pe-value');require(close(actual,expected,.0001),'位置编码公式错误');const hash=await frame.locator('#pe-canvas').evaluate(c=>{const ctx=c.getContext('2d');return [...ctx.getImageData(0,0,c.width,c.height).data].filter((v,i)=>i%4!==3&&v>0).length;});require(hash>1000,'Canvas没有真实绘制热力图');await frame.locator('#pe-canvas').click({position:{x:100,y:60}});const after=await scalar('pe-value');require(Number.isFinite(after),'点击热力图无法读取值');return {actual,expected,coloredChannels:hash,after};});
 await shot('desktop-position','#positional-encoding');
 await check('复杂度公式、视觉与口径',async()=>{await set('complexity-n',200);await set('complexity-d',512);const v=await values('complexity-values'),expected=[200*200*512,200*512*512,3*200*512*512];require(v.every((n,i)=>close(n,expected[i])),'复杂度表达式计算错误');const b=await bars('[data-complexity-index]');require(b.length===3&&b.some(n=>n.height>10&&n.width>10),'复杂度图形没有渲染');return {v,b};});
 await check('真实BLEU图与任务切换',async()=>{await frame.locator('#result-task').selectOption('ende');let b=await bars('[data-bleu][data-model]');require(b.length>=5,'BLEU图缺少模型');require(b.every(v=>Number.isFinite(Number(v.value))&&v.height>2),'BLEU图出现空值/无效高度');const de=b.map(v=>Number(v.value));require(de.includes(28.4)&&de.includes(27.3),'EN-DE报告值缺失');await frame.locator('#result-task').selectOption('enfr');b=await bars('[data-bleu][data-model]');const fr=b.map(v=>Number(v.value));require(fr.includes(41.8)&&!fr.includes(28.4),'切换语言任务未换对应数据');return {de,fr};});
 await check('消融只选真实行，不合成联合结果',async()=>{const options=await frame.locator('#ablation-config option').evaluateAll(es=>es.map(e=>({value:e.value,text:e.textContent})));const first=options.find(o=>/1\s*(head|头)|单头|h\s*=\s*1\b/i.test(o.text));require(first,'没有可选单头实验行');await frame.locator('#ablation-config').selectOption(first.value);const v=await values('ablation-result');require(close(v[0],24.9)&&close(v[1],5.29),'单头消融结果不是原表的24.9/5.29');return {options,oneHead:v};});
 await shot('desktop-evidence','#mt-results');
 await check('来源、概念与提问桥接',async()=>{await page.evaluate(()=>{window.pmMessages=[];window.addEventListener('message',e=>window.pmMessages.push(e.data));});await frame.locator('button[data-source]').first().click();await frame.locator('button[data-ask]').first().click();if(await frame.locator('button[data-concept]').count())await frame.locator('button[data-concept]').first().click();const messages=await page.evaluate(()=>window.pmMessages);require(messages.some(m=>m.type==='cite'&&m.id),'来源未桥接');require(messages.some(m=>m.type==='ask'&&m.node&&m.text),'提问未桥接');return messages.filter(m=>['cite','ask','concept'].includes(m.type));});
 await check('独立运行无网络与初始化异常',async()=>{require(report.errors.length===0,JSON.stringify(report.errors));require(report.requests.length===0,'请求了外部资源');const body=await frame.locator('body').innerText();require(!/\bNaN\b|\bInfinity\b/.test(body),'画面出现非有限值');});
 for(const width of [736,390,320])await check('响应式 '+width,async()=>{await page.setViewportSize({width,height:920});await frame.locator('body').evaluate(()=>scrollTo(0,0));const size=await frame.locator('body').evaluate(()=>({viewport:innerWidth,body:document.body.scrollWidth,document:document.documentElement.scrollWidth}));if(width===390){await shot('mobile-hero');await shot('mobile-attention','#scaled-dot-product');}require(size.document<=size.viewport+1,'页面横向溢出：'+JSON.stringify(size));return size;});
 await check('CSP/沙箱边界',async()=>{const markup=readFileSync(input,'utf8');require(markup.includes("connect-src 'none'")&&markup.includes("worker-src 'none'"),'CSP缺失');const sandbox=await page.locator('iframe').getAttribute('sandbox');require(sandbox==='allow-scripts','沙箱权限过宽');const origin=await frame.locator('body').evaluate(()=>{try{return parent.document.body.textContent;}catch(e){return 'blocked';}});require(origin==='blocked','可以访问宿主DOM');return {sandbox,parentAccess:origin};});
}catch(e){report.issues.push({name:'initialization',detail:e.message});}
finally{report.status=report.issues.length?'failed':'pass';writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify({status:report.status,checks:report.checks.length,issues:report.issues},null,2));}
