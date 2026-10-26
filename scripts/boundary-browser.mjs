import {chromium} from 'playwright-core';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
const base='http://127.0.0.1:8000';
const manifest=JSON.parse(readFileSync('tests/corpus/manifest.json','utf8'));
const report={phase:'before_fixes',browser:'Microsoft Edge / Playwright; Browser plugin not available',checks:[],errors:[]};
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
mkdirSync('artifacts',{recursive:true});
let current;
page.on('pageerror',e=>report.errors.push({case:current,error:e.message}));
for(const test of manifest.papers){
 current=test.id;
 const previous=JSON.parse(readFileSync(`data/benchmark-live/${test.id}.json`,'utf8'));
 const row={case:test.id,document_id:previous.document_id,issues:[]};
 try{
  const doc=await(await fetch(`${base}/api/documents/${previous.document_id}`)).json();
  await page.goto(`${base}/?document=${doc.id}`);
  await page.getByRole('heading',{name:doc.title,exact:true}).waitFor({timeout:20000});
  row.title=doc.title;row.status=doc.status;row.rendered_nodes=await page.locator('.reading-section').count();row.expected_nodes=doc.nodes.length;
  if(row.rendered_nodes!==row.expected_nodes)row.issues.push('node_count_mismatch');
  if(doc.nodes.length===0)row.issues.push('no_readable_generated_nodes');
  row.identity={url:page.url(),title:await page.title()};
  await page.getByRole('button',{name:'原始 PDF',exact:true}).click();
  await page.locator('.pdf-page-area img').waitFor({timeout:20000});
  row.original_image=await page.locator('.pdf-page-area img').evaluate(e=>new Promise(resolve=>{if(e.complete)resolve(e.naturalWidth>0);else{e.onload=()=>resolve(e.naturalWidth>0);e.onerror=()=>resolve(false)}}));
  if(!row.original_image)row.issues.push('original_image_missing');
  await page.getByRole('button',{name:'交互讲解',exact:true}).click();
  row.widths={};
  for(const width of [1440,736,390,320]){
   await page.setViewportSize({width,height:900});
   row.widths[width]=await page.locator('.reading-scroll').evaluate(e=>({scroll:e.scrollWidth,client:e.clientWidth}));
   if(row.widths[width].scroll>row.widths[width].client+2)row.issues.push(`horizontal_overflow_${width}`);
  }
  if(['cnnic55','adaptive-dcs-somp','simulation-argument'].includes(test.id))await page.screenshot({path:`artifacts/boundary-${test.id}.png`,fullPage:true});
  row.status_of_test='tested';
 }catch(e){row.status_of_test='failed';row.issues.push(e.message)}
 report.checks.push(row);writeFileSync('artifacts/boundary-browser.json',JSON.stringify(report,null,2));console.log(test.id,row.status_of_test,JSON.stringify(row.issues));
}
await browser.close();
