/* Trusted host bridge. Authors only access read-only evidence and local DOM. */
(()=>{
 const C=PM_CONFIG;
 const embedded=parent!==window&&!C.standalone;
 const deepFreeze=o=>{if(o&&typeof o==='object'){Object.values(o).forEach(deepFreeze);Object.freeze(o);}return o;};
 Object.defineProperty(window,'paperMindData',{value:deepFreeze(C.data),writable:false,configurable:false});
 const nodes=new Set(C.data.nodes.map(n=>n.id)),concepts=new Set(C.data.nodes.flatMap(n=>n.concepts));
 let initialized=false,height=0,scheduled=false;
 function emit(type,payload={}){if(embedded)parent.postMessage({type,edition:C.edition,document:C.document,channel:C.channel,...payload},'*');}
 function measure(){if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;const h=Math.ceil(document.documentElement.scrollHeight);if(h!==height){height=h;emit('resize',{height:h});}});}
 function source(id){const s=C.data.sources[id];if(!s)return;if(embedded){emit('cite',{id:s.id});return;}document.getElementById('pm-local-source')?.remove();const box=document.createElement('aside');box.id='pm-local-source';box.setAttribute('role','dialog');box.setAttribute('aria-label','原文出处');const title=document.createElement('strong');title.textContent='原文 · 第 '+s.page+' 页';const quote=document.createElement('blockquote');quote.textContent=s.quote;const close=document.createElement('button');close.textContent='返回讲解';close.addEventListener('click',()=>box.remove());box.append(title,quote,close);document.body.append(box);close.focus();}
 function nodeOf(el){return el.closest('[data-node]')?.dataset.node||C.data.nodes[0]?.id;}
 function readingTools(){for(const b of document.querySelectorAll('button[data-source]')){const s=C.data.sources[b.dataset.source];if(s)b.textContent='原文 · p.'+s.page;}if(!embedded){for(const b of document.querySelectorAll('[data-ask],[data-concept],[data-undo]'))b.hidden=true;return;}for(const n of C.data.nodes){const anchor=document.getElementById(n.id);if(!anchor||anchor.querySelector('button[data-ask]'))continue;const tools=document.createElement('div');tools.className='pm-reading-tools';tools.dataset.node=n.id;const ask=document.createElement('button');ask.dataset.ask='请解释'+n.title+'的原理、推导与成立条件';ask.textContent='沿着这里继续问';tools.append(ask);for(const id of n.concepts||[]){const b=document.createElement('button');b.dataset.concept=id;b.textContent=C.data.concepts?.[id]?.title||'查阅相关概念';tools.append(b);}anchor.append(tools);}}
 document.addEventListener('click',event=>{
  const button=event.target.closest('button,a');if(!button)return;
  if(button.dataset.source){event.preventDefault();source(button.dataset.source);}
  else if(button.dataset.concept&&concepts.has(button.dataset.concept))emit('concept',{id:button.dataset.concept,node:nodeOf(button)});
  else if(button.dataset.ask&&event.isTrusted)emit('ask',{text:button.dataset.ask.slice(0,2000),node:nodeOf(button)});
  else if(button.dataset.undo&&event.isTrusted)emit('undo',{id:button.dataset.undo});
  else if(button.matches('a[href^="#"]')){event.preventDefault();const el=document.getElementById(button.getAttribute('href').slice(1));if(el){if(!embedded)el.scrollIntoView();else emit('scroll',{top:el.getBoundingClientRect().top+scrollY});}}
 });
 document.addEventListener('mouseup',()=>{const text=window.getSelection()?.toString().trim();if(text&&text.length>=4&&text.length<=2000)emit('selection',{text,node:nodeOf(window.getSelection()?.anchorNode?.parentElement||document.body)});});
 function supplements(items){document.querySelectorAll('.pm-user-note').forEach(n=>n.remove());for(const item of items){if(!nodes.has(item.node_id))continue;const anchor=document.getElementById(item.node_id);if(!anchor)continue;const note=document.createElement('aside');note.className='pm-user-note';note.dataset.node=item.node_id;const h=document.createElement('h4');h.textContent='我的讲解补充';const p=document.createElement('p');p.textContent=item.text;note.append(h,p);for(const id of item.source_ids||[]){const alias=Object.keys(C.data.sources).find(k=>C.data.sources[k].id===id);if(alias){const b=document.createElement('button');b.dataset.source=alias;b.textContent='原文 · p.'+C.data.sources[alias].page;note.append(b);}}if(item.can_undo){const b=document.createElement('button');b.dataset.undo=item.id;b.textContent='撤回补充';note.append(b);}anchor.append(note);}measure();}
 window.addEventListener('message',event=>{const d=event.data;if(event.source!==parent||!d||d.channel!==C.channel)return;
  if(d.type==='navigate'&&nodes.has(d.node)){const el=document.getElementById(d.node);if(el){for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;emit('scroll',{top:el.getBoundingClientRect().top+scrollY});}}
  if(d.type==='viewport'&&Number.isFinite(d.top)){let chosen=C.data.nodes[0]?.id;for(const n of C.data.nodes){const el=document.getElementById(n.id);if(el&&el.getBoundingClientRect().top+scrollY<=d.top+160)chosen=n.id;}if(chosen)emit('active',{node:chosen});}
  if(d.type==='supplements'&&Array.isArray(d.items))supplements(d.items.slice(0,100));
 });
 window.addEventListener('pm-initialized',()=>{readingTools();initialized=true;document.body.dataset.pmReady='true';emit('ready');measure();});
 window.addEventListener('error',event=>{document.body.dataset.pmError=String(event.message);emit('error',{message:String(event.message).slice(0,300)});});
 new ResizeObserver(measure).observe(document.body);measure();
})();
