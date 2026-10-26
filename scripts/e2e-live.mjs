import { chromium } from 'playwright-core';
import {existsSync,mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const base=process.env.PAPERMIND_LIVE_URL||'http://127.0.0.1:8000';
const request=async(url,options)=>{const r=await fetch(base+'/api'+url,options);if(!r.ok)throw Error(await r.text());return r.json();};
const bootstrap=await request('/bootstrap');
const chosen=process.env.PAPERMIND_TEST_DOCUMENT||bootstrap.documents.find(d=>!d.is_demo&&d.status==='ready')?.id;
if(!chosen)throw Error('No real ready document available for browser verification');
const doc=await request('/documents/'+chosen);
const browser=await chromium.launch({channel:'msedge',headless:true});
const report={document_id:chosen,title:doc.title,status:'running',checks:[],errors:[]};
mkdirSync('artifacts',{recursive:true});
const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
page.on('pageerror',e=>report.errors.push(e.message));
try{
  await page.goto(base+'/?document='+chosen);
  await page.getByRole('heading',{name:doc.title,exact:true}).waitFor();
  assert.equal(await page.locator('.reading-section').count(),doc.nodes.length);
  console.log('live checkpoint',report.checks.length+1);report.checks.push('真实讲解完整渲染，非预置样例');
  const initialLibrary=await request('/bootstrap');
  if(await page.locator('.concept-links button').count()){
    await page.locator('.concept-links button').first().click();
    await page.locator('.concept-title').waitFor();
    const firstId=doc.nodes.find(n=>n.concepts.length)?.concepts[0];
    if(firstId&&!initialLibrary.library.some(i=>i.concept_id===firstId)){
      await page.getByRole('button',{name:'加入个人概念库',exact:true}).click();
      await page.getByRole('button',{name:'已加入概念库 · 点击移出',exact:true}).waitFor();
      await page.getByRole('button',{name:'已加入概念库 · 点击移出',exact:true}).click();
      await page.getByRole('button',{name:'加入个人概念库',exact:true}).waitFor();
    }
    console.log('live checkpoint',report.checks.length+1);report.checks.push('真实概念查阅、保存与移出');
  }
  await page.locator('.section-sources .citation').first().click();
  await page.locator('.rightbar .source-entry blockquote').waitFor();
  assert((await page.locator('.rightbar .source-entry blockquote').innerText()).length>30);
  console.log('live checkpoint',report.checks.length+1);report.checks.push('真实来源原句回查');
  await page.getByRole('button',{name:'原始 PDF',exact:true}).click();
  await page.locator('.pdf-page-area img').waitFor();
  await page.locator('.pdf-page-area img').evaluate(async e=>{await Promise.race([e.decode(),new Promise((_,reject)=>setTimeout(()=>reject(Error('PDF image decode timed out')),30000))]);if(!e.naturalWidth)throw Error('PDF page image has no pixels');});
  await page.locator('.pdf-controls').scrollIntoViewIfNeeded();
  const box=await page.locator('.pdf-page-area').boundingBox();
  await page.mouse.move(box.x+box.width*.15,box.y+45);await page.mouse.down();await page.mouse.move(box.x+box.width*.6,box.y+120,{steps:8});await page.mouse.up();
  await page.locator('.pdf-selection-box').waitFor();
  await page.getByRole('button',{name:'问所选区域',exact:true}).click();
  await page.locator('.companion-tabs').getByRole('button',{name:'Copilot',exact:true}).waitFor();
  assert.match(await page.locator('.composer-selection').innerText(),/第.*页所选区域/);
  console.log('live checkpoint',report.checks.length+1);report.checks.push('真实PDF页图加载、框选与提问上下文');
  await page.getByRole('button',{name:'交互讲解',exact:true}).click();
  const stepsIndex=doc.nodes.findIndex(n=>n.kind==='steps'&&(n.steps||[]).length>1);
  if(stepsIndex>=0){
    await page.locator('.outline button').nth(stepsIndex).click();
    await page.getByLabel('移除页面选择').click();
    await page.getByLabel('向 Copilot 提问').fill('请把当前演示推进下一步，并解释这一步与前一步的关系。');
    const responseWait=page.waitForResponse(r=>r.url().endsWith(`/documents/${chosen}/copilot/runs`)&&r.request().method()==='POST',{timeout:300000});
    await page.getByRole('button',{name:'发送问题',exact:true}).click();
    const response=await responseWait;assert.equal(response.status(),202,await response.text());
    const created=await response.json();let run;
    for(let attempt=0;attempt<600;attempt++){run=await request(`/copilot/runs/${created.id}`);if(['completed','failed','cancelled'].includes(run.status))break;await new Promise(resolve=>setTimeout(resolve,500));}
    assert.equal(run.status,'completed',JSON.stringify(run));
    const refreshed=await request('/documents/'+chosen),assistant=refreshed.messages.find(message=>message.id===run.assistant_message_id);
    report.live_turn={provider:assistant.provider,action:assistant.action,verification:assistant.verification};
    assert.equal(assistant.provider,'qwen');await page.locator('.message.assistant').last().waitFor({timeout:300000});
    if(assistant.action?.type==='next_step'){
      await page.locator(`#${doc.nodes[stepsIndex].id} .step-tabs button`).nth(1).waitFor();
      assert.equal(await page.locator(`#${doc.nodes[stepsIndex].id} .step-tabs button`).nth(1).getAttribute('aria-pressed'),'true');
      console.log('live checkpoint',report.checks.length+1);report.checks.push('真实千问对话驱动步骤演示，前端执行并记录回执');
    }else report.errors.push('明确推进演示的请求没有生成next_step动作');
  }
  await page.screenshot({path:'artifacts/live-desktop.png',fullPage:true});
  for(const width of [1024,736,390,320]){
    await page.setViewportSize({width,height:900});
    const overflow=await page.locator('.reading-scroll').evaluate(e=>({scroll:e.scrollWidth,client:e.clientWidth}));
    assert(overflow.scroll<=overflow.client+2,`Reading overflow ${width}: ${JSON.stringify(overflow)}`);
  }
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'artifacts/live-mobile.png',fullPage:true});
  console.log('live checkpoint',report.checks.length+1);report.checks.push('真实论文在1024/736/390/320阅读区没有水平溢出');
  assert.deepEqual(report.errors,[]);
  report.status='passed';
  console.log(JSON.stringify(report,null,2));
}catch(error){
  report.status='failed';report.errors.push(error.message);throw error;
}finally{
  writeFileSync('artifacts/live-browser-report.json',JSON.stringify(report,null,2));await browser.close();
}
