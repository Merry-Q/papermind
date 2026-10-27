import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, BookMarked, BookOpen, Check, CheckCheck, ChevronDown, ChevronRight, CircleHelp, FileText, GitBranch, Layers3, Library, Link2, LoaderCircle, MessageSquare, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, Plus, RotateCcw, Send, Settings2, ShieldCheck, Sparkles, Trash2, Upload, X } from 'lucide-react';
import { api, json } from './api';
import Mechanism from './Mechanism';
import {LiveSteps,VisualFigure,PDFRegionReader,RichText} from './LiveReading';
import CopilotRunCard,{CopilotTimeline} from './CopilotRunCard';
import ReadingV2 from './ReadingV2';
import type { Bootstrap, Concept, CopilotEvent, CopilotMode, CopilotRun, Document, Message, Patch, Scope, Source } from './types';

type Pane = 'knowledge'|'chat'|'library'|'sources'|'ledger';
type Notice = {text:string;memoryId?:string};
const LAYERS:Record<string,string>={definition:'定义',intuition:'直觉与机制'};

export default function App() {
  const [boot,setBoot]=useState<Bootstrap|null>(null),[doc,setDoc]=useState<Document|null>(null);
  const [docId,setDocId]=useState(()=>new URLSearchParams(window.location.search).get('document')||localStorage.getItem('papermind-document')||''),[reload,setReload]=useState(0),[loading,setLoading]=useState(true);
  const [pane,setPane]=useState<Pane>('knowledge'),[stack,setStack]=useState<string[]>([]),[active,setActive]=useState('problem');
  const [editionConcept,setEditionConcept]=useState<Concept|null>(null);
  const [view,setView]=useState<'reading'|'original'>('reading'),[selectedSource,setSelectedSource]=useState<string|null>(null);
  const [scope,setScope]=useState<Scope>('local'),[previous,setPrevious]=useState<Scope|null>(null);
  const [question,setQuestion]=useState(''),[selection,setSelection]=useState<string|null>(null),[busy,setBusy]=useState('');
  const [notice,setNotice]=useState<Notice|null>(null),[error,setError]=useState(''),[preview,setPreview]=useState<Patch|null>(null);
  const [mobileNav,setMobileNav]=useState(false),[mobilePane,setMobilePane]=useState(false),[attachOpen,setAttachOpen]=useState(false);
  const [showSaved,setShowSaved]=useState(false);
  const [leftCollapsed,setLeftCollapsed]=useState(false),[rightCollapsed,setRightCollapsed]=useState(false);
  const [viewportWidth,setViewportWidth]=useState(()=>window.innerWidth);
  const leftOpen=viewportWidth<=680?mobileNav:!leftCollapsed;
  const rightOpen=viewportWidth<=1020?mobilePane:!rightCollapsed;
  useEffect(()=>{const resize=()=>setViewportWidth(window.innerWidth);window.addEventListener('resize',resize);return()=>window.removeEventListener('resize',resize);},[]);
  function toggleLeft(){if(window.innerWidth<=680)setMobileNav(v=>!v);else setLeftCollapsed(v=>!v);}
  function toggleRight(){if(window.innerWidth<=1020)setMobilePane(v=>!v);else setRightCollapsed(v=>!v);}
  const [selectedPage,setSelectedPage]=useState<number|null>(null),[selectedBox,setSelectedBox]=useState<number[]|null>(null);
  const [stepStates,setStepStates]=useState<Record<string,number>>({});
  const [v2Edition,setV2Edition]=useState(()=>new URLSearchParams(window.location.search).get('readingV2')||'');
  const [v2Document,setV2Document]=useState(()=>new URLSearchParams(window.location.search).get('document'));
  const [publishedV2,setPublishedV2]=useState('');
  const [editionResolving,setEditionResolving]=useState(true);
  const classicDocuments=useRef(new Set<string>());
  const currentDocument=useRef(docId);currentDocument.current=docId;
  const useV2=Boolean(v2Edition)&&doc?.id===v2Document;
  const [capability,setCapability]=useState<{mode:string;models:Record<string,string>;chat_context_version?:number}|null>(null);
  const [copilotMode,setCopilotMode]=useState<CopilotMode>('auto'),[copilotRun,setCopilotRun]=useState<CopilotRun|null>(null),[copilotEvents,setCopilotEvents]=useState<CopilotEvent[]>([]);
  const [timelineOpen,setTimelineOpen]=useState<string|null>(null),[messageTimelines,setMessageTimelines]=useState<Record<string,CopilotEvent[]>>({});
  const fileRef=useRef<HTMLInputElement>(null),chatEnd=useRef<HTMLDivElement>(null),readingPosition=useRef(0),handledRun=useRef<string|null>(null);
  const bootRefresh=async()=>{const b=await api<Bootstrap>('/bootstrap');setBoot(b);return b;};

  useEffect(()=>{
    const controller=new AbortController();
    readingPosition.current=0;handledRun.current=null;setLoading(true);setError('');setDoc(null);setPreview(null);setView('reading');setStack([]);setEditionConcept(null);setScope('local');setPrevious(null);setActive('problem');setSelectedSource(null);setSelection(null);setShowSaved(false);setAttachOpen(false);setPane('knowledge');setMobilePane(false);setSelectedPage(null);setSelectedBox(null);setCopilotRun(null);setCopilotEvents([]);setTimelineOpen(null);setMessageTimelines({});
    api<Bootstrap>('/bootstrap',{signal:controller.signal}).then(async b=>{
      if(controller.signal.aborted)return;
      setBoot(b);
      const chosen=b.documents.some(d=>d.id===docId)?docId:b.default_document_id||b.documents[0]?.id||'';
      if(!chosen){localStorage.removeItem('papermind-document');setLoading(false);return;}
      if(chosen!==docId){
        const url=new URL(window.location.href);url.searchParams.set('document',chosen);for(const key of ['reading','readingV2','readingInspection'])url.searchParams.delete(key);window.history.replaceState(null,'',url);
        setDocId(chosen);return;
      }
      localStorage.setItem('papermind-document',chosen);
      const d=await api<Document>(`/documents/${chosen}`,{signal:controller.signal});
      if(controller.signal.aborted)return;
      setDoc(d);setActive(d.nodes[0]?.id||(d.is_demo?'problem':'document'));setLoading(false);
    }).catch(e=>{if(e.name!=='AbortError'){setError(e.message);setLoading(false);}});
    return()=>controller.abort();
  },[docId,reload]);
  useEffect(()=>{
    setV2Edition('');setPublishedV2('');setV2Document(docId);setEditionResolving(true);
    if(!doc||doc.id!==docId||doc.is_demo){setEditionResolving(false);return;}
    const params=new URLSearchParams(window.location.search),sameDocument=params.get('document')===docId;
    const classic=classicDocuments.current.has(docId)||(sameDocument&&params.get('reading')==='classic');
    const explicit=sameDocument?params.get('readingV2'):null;
    if(classic||explicit)setEditionResolving(false);
    if(explicit&&!classic)setV2Edition(explicit);
    const controller=new AbortController();
    api<{id:string;document_id:string}|null>(`/documents/${docId}/reading-v2/default`,{signal:controller.signal}).then(value=>{
      if(controller.signal.aborted||currentDocument.current!==docId)return;
      if(value?.document_id===docId){setPublishedV2(value.id);const url=new URLSearchParams(window.location.search),nowClassic=classicDocuments.current.has(docId)||(url.get('document')===docId&&url.get('reading')==='classic');if(!classic&&!nowClassic&&!explicit)setV2Edition(value.id);}
    }).catch(()=>{}).finally(()=>{if(!controller.signal.aborted&&currentDocument.current===docId)setEditionResolving(false);});
    return()=>controller.abort();
  },[docId,doc?.id,doc?.status,doc?.reading_job?.id,doc?.reading_job?.status]);
  useEffect(()=>{api<{mode:string;models:Record<string,string>;chat_context_version?:number}>('/capabilities').then(setCapability).catch(()=>{});},[]);
  useEffect(()=>{
    if(![doc?.job?.status,doc?.reading_job?.status].some(status=>status&&['queued','running'].includes(status)))return;
    const controller=new AbortController();
    const timer=window.setInterval(()=>{api<Document>(`/documents/${docId}`,{signal:controller.signal}).then(next=>{setDoc(next);setActive(id=>next.nodes.some(n=>n.id===id)?id:(next.nodes[0]?.id||(next.is_demo?'problem':'document')));return bootRefresh();}).catch(e=>{if(e.name!=='AbortError')setError(e.message);});},3000);
    return()=>{controller.abort();window.clearInterval(timer);};
  },[docId,doc?.job?.status,doc?.reading_job?.status]);
  useLayoutEffect(()=>{if(view==='reading'&&!loading)window.document.querySelector('.reading-scroll')?.scrollTo({top:readingPosition.current,behavior:'instant'});},[view,loading]);
  useEffect(()=>{chatEnd.current?.scrollIntoView({block:'nearest'});},[doc?.messages.length,pane,copilotRun?.status,copilotRun?.plan_revision,copilotEvents.length]);
  useEffect(()=>{if(!notice||notice.memoryId)return;const t=window.setTimeout(()=>setNotice(null),4500);return()=>clearTimeout(t);},[notice]);
  useEffect(()=>{
    if(!doc)return;let disposed=false;
    api<CopilotRun|null>(`/documents/${docId}/copilot/runs/active`).then(async value=>{if(disposed||!value)return;setCopilotRun(value);const payload=await api<{events:CopilotEvent[]}>(`/copilot/runs/${value.id}/events`);if(!disposed)setCopilotEvents(payload.events);}).catch(()=>{});
    return()=>{disposed=true;};
  },[docId,doc?.id]);
  useEffect(()=>{
    if(!copilotRun||['awaiting_user','completed','failed','cancelled'].includes(copilotRun.status))return;
    let disposed=false,timer:number|undefined;
    const poll=async()=>{try{
      const after=copilotEvents.at(-1)?.event_id||0;
      const [next,payload]=await Promise.all([api<CopilotRun>(`/copilot/runs/${copilotRun.id}`),api<{events:CopilotEvent[]}>(`/copilot/runs/${copilotRun.id}/events?after=${after}`)]);
      if(disposed)return;
      if(payload.events.length)setCopilotEvents(previous=>[...previous,...payload.events.filter(event=>!previous.some(item=>item.event_id===event.event_id))]);
      setCopilotRun(next);
      if(next.status==='completed'&&handledRun.current!==next.id){
        handledRun.current=next.id;const fresh=await refreshDoc();const assistant=fresh.messages.find(message=>message.id===next.assistant_message_id);
        if(assistant){setMessageTimelines(value=>({...value,[assistant.id]:[...copilotEvents,...payload.events]}));await applyAssistantAction(assistant,fresh);}
        if(next.new_memory){await bootRefresh();setNotice({text:`已记住：${next.new_memory.text}`,memoryId:next.new_memory.id});}
        setCopilotRun(null);setCopilotEvents([]);return;
      }
      if(!['completed','failed','cancelled','awaiting_user'].includes(next.status))timer=window.setTimeout(poll,900);
    }catch(e){if(!disposed)setError(e instanceof Error?e.message:'无法读取 Copilot 进度');}};
    void poll();return()=>{disposed=true;if(timer)window.clearTimeout(timer);};
  },[copilotRun?.id,copilotRun?.status,copilotEvents.at(-1)?.event_id]);
  useEffect(()=>{
    if(!doc||view!=='reading')return;
    const observer=new IntersectionObserver(entries=>{const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio);if(visible[0])setActive(visible[0].target.id);},{root:window.document.querySelector('.reading-scroll'),threshold:[0.1,0.4,0.8],rootMargin:'-12% 0px -45% 0px'});
    window.document.querySelectorAll('.reading-section').forEach(el=>observer.observe(el));return()=>observer.disconnect();
  },[doc,view]);

  async function run(key:string, work:()=>Promise<void>) {if(busy)return;setBusy(key);setError('');try{await work();}catch(e){setError(e instanceof Error?e.message:'操作失败，请重试');}finally{setBusy('');}}
  async function refreshDoc(){const d=await api<Document>(`/documents/${docId}`);setDoc(d);return d;}
  function navigate(id:string){setActive(id);setMobileNav(false);setView('reading');window.setTimeout(()=>{if(useV2)window.dispatchEvent(new CustomEvent('papermind-v2-navigate',{detail:{id}}));else window.document.getElementById(id)?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});},40);}
  function showPane(next:Pane){setPane(next);if(window.innerWidth<=1020)setMobilePane(true);else setRightCollapsed(false);}
  function exitV2(){
    classicDocuments.current.add(docId);setV2Edition('');setEditionResolving(false);readingPosition.current=0;
    const url=new URL(window.location.href);url.searchParams.set('document',docId);url.searchParams.set('reading','classic');url.searchParams.delete('readingV2');url.searchParams.delete('readingInspection');window.history.replaceState(null,'',url);
  }
  function openPublishedV2(){classicDocuments.current.delete(docId);setV2Edition(publishedV2);readingPosition.current=0;const url=new URL(window.location.href);url.searchParams.set('document',docId);url.searchParams.delete('reading');url.searchParams.delete('readingV2');url.searchParams.delete('readingInspection');window.history.replaceState(null,'',url);}
  function changeDocument(id:string){setDocId(id);const url=new URL(window.location.href);url.searchParams.set('document',id);for(const key of ['reading','readingV2','readingInspection'])url.searchParams.delete(key);window.history.replaceState(null,'',url);}
  function concept(id:string,fallback?:Concept){setEditionConcept(fallback||null);setStack([id]);setShowSaved(false);showPane('knowledge');}
  function cite(id:string){setSelectedSource(id);showPane('sources');}
  function changeScope(next:Scope){setPrevious(scope);setScope(next);}
  function restoreScope(){if(previous){const old=scope;setScope(previous);setPrevious(old);}}
  function ask(text?:string,selected?:string){setQuestion(text||'');setSelection(selected||null);setSelectedPage(null);setSelectedBox(null);showPane('chat');}
  function askRegion(page:number,bbox?:number[]){ask('请解释所选图表或公式，说明适用条件与识别局限。');setSelectedPage(page);setSelectedBox(bbox||null);}
  async function generate(){await run('generate',async()=>{await api(doc?.canonical_complete?`/documents/${docId}/reading-v2`:`/documents/${docId}/generation`,json('POST',{}));await refreshDoc();});}
  async function expandKnowledge(){if(!currentConcept)return;await run('expand',async()=>{const card=await api<{id:string}>(`/documents/${docId}/knowledge`,json('POST',{concept_id:currentConcept.id,question:currentConcept.next_question||null}));await bootRefresh();await refreshDoc();setStack(v=>[...v,card.id]);setShowSaved(false);});}
  async function applyAssistantAction(assistant:Message,baseDoc:Document){
    if(!assistant.action)return;const action=assistant.action;
    if(action.type==='set_search_scope'){changeScope(action.scope);navigate('mechanism');return;}
    const target=baseDoc.nodes.find(node=>node.id===action.node_id),count=target?.steps?.length||0,valid=count>1;
    if(valid){setStepStates(states=>({...states,[action.node_id]:action.type==='reset_steps'?0:Math.max(0,Math.min(count-1,(states[action.node_id]||0)+(action.type==='next_step'?1:-1)))}));navigate(action.node_id);}
    await api(`/documents/${docId}/actions/${action.id}/result`,json('POST',{status:valid?'executed':'rejected',detail:valid?'步骤状态已更新':'当前演示不存在或没有可切换步骤'}));
  }
  async function send(text=question){
    if(!doc||!text.trim()||(copilotRun&&!['completed','failed','cancelled'].includes(copilotRun.status)))return;
    await run('chat',async()=>{
      const result=await api<CopilotRun>(`/documents/${docId}/copilot/runs`,json('POST',{text:text.trim(),node_id:doc.nodes.some(n=>n.id===active)?active:(doc.is_demo?'problem':'document'),selected_text:selection,selected_page:selectedPage,bbox:selectedBox,current_step:stepStates[active]||0,mode:copilotMode}));
      setDoc({...doc,messages:[...doc.messages,result.user_message]});setCopilotRun(result);setCopilotEvents([]);handledRun.current=null;setQuestion('');setSelection(null);setSelectedPage(null);setSelectedBox(null);
    });
  }
  async function decideCopilot(action:'approve_plan'|'revise_plan',comment?:string){if(!copilotRun)return;await run('copilot-decision',async()=>{const next=await api<CopilotRun>(`/copilot/runs/${copilotRun.id}/decision`,json('POST',{action,comment:comment||null}));setCopilotRun(next);});}
  async function cancelCopilot(){if(!copilotRun)return;await run('copilot-cancel',async()=>setCopilotRun(await api<CopilotRun>(`/copilot/runs/${copilotRun.id}/cancel`,json('POST',{}))));}
  async function toggleTimeline(message:Message){
    if(!message.run_id)return;if(timelineOpen===message.id){setTimelineOpen(null);return;}
    setTimelineOpen(message.id);if(messageTimelines[message.id])return;
    try{const payload=await api<{events:CopilotEvent[]}>(`/copilot/runs/${message.run_id}/events`);setMessageTimelines(value=>({...value,[message.id]:payload.events}));}catch(e){setError(e instanceof Error?e.message:'无法读取研究过程');}
  }
  async function saveConcept(id:string){await run('save',async()=>{await api('/library',json('PUT',{document_id:docId,concept_id:id}));await bootRefresh();setNotice({text:'已加入个人概念库；以后可跳过这一层解释'});});}
  async function removeConcept(id:string){await run('remove',async()=>{await api(`/library/${encodeURIComponent(id)}`,{method:'DELETE'});await bootRefresh();setNotice({text:'已移出概念库，下次会再次提供解释'});});}
  async function forget(id:string){await run('forget',async()=>{await api(`/memories/${id}`,{method:'DELETE'});await bootRefresh();setNotice({text:'已撤销这条解释偏好'});});}
  async function previewMessage(message:Message){if(!doc)return;await run('preview',async()=>{const p=await api<Patch>(`/documents/${docId}/patches`,json('POST',{message_id:message.id,base_revision:doc.revision}));setPreview(p);});}
  async function applyPatch(){if(!doc||!preview)return;await run('patch',async()=>{await api(`/documents/${docId}/patches/${preview.id}/apply`,json('POST',{base_revision:doc.revision}));await refreshDoc();setPreview(null);setNotice({text:'补充已加入页面，个人概念库未改变'});});}
  async function undoPatch(){if(!doc||!doc.supplements.length)return;await run('undo',async()=>{await api(`/documents/${docId}/patches/${doc.supplements.at(-1)!.id}/undo`,json('POST',{base_revision:doc.revision}));await refreshDoc();setNotice({text:'已撤回最近一次页面补充'});});}
  async function upload(file:File){await run('upload',async()=>{const form=new FormData();form.append('file',file);const result=await api<{id:string}>('/documents',{method:'POST',body:form});changeDocument(result.id);setReload(v=>v+1);setNotice({text:capability?.mode==='live'?'已导入 PDF，正在生成整篇交互讲解':'已抽取 PDF 文本；请先在后端配置千问凭证'});});}
  async function attach(id:string){await run('attach',async()=>{await api(`/documents/${docId}/attachments`,json('POST',{document_id:id}));await refreshDoc();setAttachOpen(false);setNotice({text:'已附加参考文献，可在当前对话比较'});});}
  function openChecks(){showPane('ledger');}

  const currentConcept=stack.length?(boot?.concepts[stack.at(-1)!]|| (editionConcept?.id===stack.at(-1)?editionConcept:null)):null;
  const conceptIsCurrent=Boolean(currentConcept&&doc?.concepts?.[currentConcept.id]);
  const saved=Boolean(currentConcept&&boot?.library.some(i=>i.concept_id===currentConcept.id&&i.layer===currentConcept.layer));
  const generationBanner = (doc&&!doc.is_demo&&<div className="generation-bar"><div><strong>{[doc.job?.status,doc.reading_job?.status].some(status=>status&&['queued','running'].includes(status))?'正在生成整篇交互讲解':doc.reading_job?.status==='failed'?'交互讲解生成未完成':publishedV2?'整篇交互讲解已生成':'讲解尚未生成完成'}</strong><span>{doc.job&&['queued','running'].includes(doc.job.status)&&doc.job.stage!=='interactive'?doc.job.detail:doc.reading_job?(doc.reading_job.error||({queued:'等待生成',planning:'正在规划全文交互',evidence:'正在提取图表数据',authoring:'正在创作交互章节',completed:'页面已生成，可开始阅读',cancelled:'生成已取消'} as Record<string,string>)[doc.reading_job.stage]||'正在生成整篇页面'):doc.job?.error||doc.job?.detail||'PDF 已保存，可开始生成'}</span></div><div className="generation-actions">{useV2&&<><button className="text-button" onClick={exitV2}>恢复原讲解</button><a href={`/api/documents/${docId}/reading-v2/${v2Edition}/export`} download>保存独立网页</a></>}{!useV2&&publishedV2&&<button className="text-button" onClick={openPublishedV2}>使用交互讲解</button>}{[doc.job?.status,doc.reading_job?.status].some(status=>status&&['queued','running'].includes(status))?<button className="text-button" onClick={()=>void run('cancel',async()=>{if(doc.reading_job&&['queued','running'].includes(doc.reading_job.status))await api(`/documents/${docId}/reading-v2/${doc.reading_job.id}/cancel`,{method:'POST'});if(doc.job&&['queued','running'].includes(doc.job.status))await api(`/jobs/${doc.job.id}/cancel`,{method:'POST'});await refreshDoc();})}>取消生成</button>:<button className="text-button" disabled={Boolean(busy)} onClick={()=>void generate()}>{publishedV2?'重新生成交互讲解':'生成 / 重试'}</button>}</div></div>);
  const allSources=[...new Map([...(doc?.sources||[]),...(doc?.attachment_sources||[]),...(boot?.concept_sources||[])].map(s=>[s.id,s])).values()];
  const currentSource=allSources.find(s=>s.id===selectedSource);
  const sourceButtons=(ids:string[])=>ids.map(id=><button className="citation" key={id} onClick={()=>cite(id)} title={allSources.find(s=>s.id===id)?.title}><Link2 size={11}/>来源 {allSources.find(s=>s.id===id)?.page||''}</button>);
  const nodeTitle=(id:string)=>id==='document'?'全文原文':doc?.nodes.find(n=>n.id===id)?.title||'当前阅读位置';
  const SourceEntry=({source}:{source:Source})=><article className="source-entry"><div className="source-meta"><span className={`source-kind ${source.kind}`}>{source.kind==='teaching'?'教学加工':source.kind==='external'?'外部知识':doc?.is_demo?'教学原文':'PDF 原文'}</span><span>{source.page>0?`第 ${source.page} 页`:'外部网页'}</span></div><h3>{source.title}</h3><blockquote>{source.quote}</blockquote><p className="muted">{source.locator}</p><div className="source-status"><CircleHelp size={13}/>{source.status==='fixture'?'作者编写的教学材料，非学术核验结果':source.status==='located'?'原文位置已定位；主张支持见核验记录':source.status==='retrieved'?'已联网读取来源正文':'模型识别内容，需对照原页'}</div>{source.url&&<a className="external-source" href={source.url} target="_blank" rel="noreferrer">打开来源网页<ArrowRight size={12}/></a>}{doc?.has_pdf&&source.page>0&&<button className="text-button" onClick={()=>{setView('original');setMobilePane(false);}}>查看 PDF 页面<ArrowRight size={13}/></button>}</article>;

  return <div className="app-shell">
    <header className="topbar"><div className="brand"><span className="brand-mark"><GitBranch size={21}/></span><span>paper<span className="brand-light">Mind</span></span></div><div className="workspace-name"><span>个人研究空间</span><ChevronRight size={14}/><strong>文献阅读</strong></div><div className="topbar-actions"><span className="local-status"><i/>{capability?.mode==='live'?'千问工作台':'未配置模型'}</span><button className="icon-button" title="个人概念库" aria-label="打开个人概念库" onClick={()=>showPane('library')}><Library size={18}/></button><span className="avatar">研</span></div></header>
    <div className={`workspace ${leftCollapsed?'left-collapsed':''} ${rightCollapsed?'right-collapsed':''}`}>
      <nav id="reading-outline" className={`leftbar ${mobileNav?'is-open':''}`} aria-label="文档与阅读目录"><div className="nav-top"><span>我的文献</span><button className="icon-button mobile-only" aria-label="关闭目录" onClick={()=>setMobileNav(false)}><X size={18}/></button></div><button className="upload-button" disabled={Boolean(busy)} onClick={()=>fileRef.current?.click()}>{busy==='upload'?<LoaderCircle className="spin" size={16}/>:<Plus size={16}/>}导入 PDF<Upload size={14}/></button><input ref={fileRef} type="file" accept="application/pdf,.pdf" hidden onChange={e=>{const file=e.target.files?.[0];if(file)void upload(file);e.target.value='';}}/>
        <div className="doc-picker"><FileText size={16}/><select aria-label="选择文档" value={docId} disabled={Boolean(busy)||loading} onChange={e=>changeDocument(e.target.value)}>{!boot?.documents.length&&<option value="">尚未导入 PDF</option>}{(boot?.documents||[]).map(d=><option key={d.id} value={d.id}>{d.title}</option>)}</select><ChevronDown size={13}/></div>
        <div className="nav-heading"><span>阅读主线</span><span>{doc?.nodes.length||0} 节</span></div><div className="outline">{doc?.nodes.map((node,index)=><button key={node.id} className={active===node.id?'active':''} onClick={()=>navigate(node.id)}><span className="outline-number">{String(index+1).padStart(2,'0')}</span><span>{['problem','mechanism','formula','evidence','limits'].includes(node.id)?({problem:'问题与全貌',mechanism:'方法如何工作',formula:'关键公式',evidence:'证据与解释',limits:'条件与局限'} as Record<string,string>)[node.id]:node.title}</span>{active===node.id&&<span className="active-dot"/>}</button>)}</div>
        <div className="nav-separator"/><button className="nav-utility" onClick={()=>showPane('library')}><BookMarked size={16}/>个人概念库<span>{boot?.library.length||0}</span></button><button className="nav-utility" onClick={()=>void openChecks()}><ShieldCheck size={16}/>原文来源<ChevronRight size={13}/></button>
        <div className="nav-bottom"><div className="note-symbol"><Layers3 size={20}/></div><strong>沿着问题，建立连接。</strong><p>在需要的地方深入，<br/>再回到论文的主线。</p><span><i/>阅读数据保存于本机</span></div>
      </nav>
      <main className="main-pane"><div className="reading-toolbar"><div className="reading-toolbar-left"><button className="icon-button sidebar-toggle" aria-label={leftOpen?'收起左侧目录':'展开左侧目录'} title={leftOpen?'收起左侧目录':'展开左侧目录'} aria-expanded={leftOpen} aria-controls="reading-outline" onClick={toggleLeft}>{leftOpen?<PanelLeftClose size={18}/>:<PanelLeftOpen size={18}/>}</button><BookOpen size={16}/><span>{doc?.type||'文献'}</span>{doc?.is_demo&&<span className="demo-tag">教学样例</span>}</div><div className="view-switch" role="group" aria-label="阅读方式"><button aria-pressed={view==='reading'} onClick={()=>setView('reading')}>交互讲解</button><button aria-pressed={view==='original'} onClick={()=>setView('original')}>{doc?.has_pdf?'原始 PDF':'教学原文'}</button></div><button className="icon-button sidebar-toggle open-companion" aria-label={rightOpen?'收起右侧阅读伴侣':'展开右侧阅读伴侣'} title={rightOpen?'收起右侧阅读伴侣':'展开右侧阅读伴侣'} aria-expanded={rightOpen} aria-controls="reading-companion" onClick={toggleRight}>{rightOpen?<PanelRightClose size={18}/>:<PanelRightOpen size={18}/>}</button></div>
{error&&<div className="error-banner" role="alert"><span>{error}</span><button className="text-button" onClick={()=>{setError('');if(!doc)setReload(v=>v+1);}}>{doc?'关闭':'重试'}</button></div>}
        {loading?<div className="loading-state"><LoaderCircle className="spin"/><p>正在打开文档…</p></div>:!doc?<div className="empty-state"><FileText size={30}/><h2>{boot&&!boot.documents.length?'导入第一篇 PDF':'尚未打开文档'}</h2><p>{boot&&!boot.documents.length?'添加论文或报告，生成整篇交互讲解。':'请检查本地服务后重试。'}</p><button className="primary-button" onClick={()=>boot&&!boot.documents.length?fileRef.current?.click():setReload(v=>v+1)}>{boot&&!boot.documents.length?'导入 PDF':'重新连接'}</button></div>:view==='original'?<div className="reading-scroll source-reading">{generationBanner}<div className="source-reader-title"><h1>{doc.has_pdf?'原始 PDF':'教学来源文档'}</h1><p>{doc.has_pdf?'原文文件保存在本机。可查看来源位置，框选图表或公式后提问。':'以下材料为 paperMind 编写的合成教学样例，不对应已发表论文。'}</p><button className="text-button" onClick={()=>setView('reading')}><ArrowLeft size={14}/>返回原阅读位置</button></div>{doc.has_pdf?<PDFRegionReader docId={doc.id} pageCount={doc.page_count} source={currentSource} onAsk={askRegion}/>:doc.sources.map(source=><SourceEntry source={source} key={source.id}/>)}</div>:<div className="reading-scroll" onScroll={e=>{readingPosition.current=e.currentTarget.scrollTop;}} onMouseUp={()=>{const selected=window.getSelection()?.toString().trim();if(selected&&selected.length>3&&selected.length<2000)setSelection(selected);}}>{generationBanner}
           {editionResolving&&!useV2?<p className="reading-v2-loading" role="status">正在打开交互讲解…</p>:useV2?<>{selection&&<div className="reading-v2-selection"><span>已选：{selection.slice(0,55)}</span><button onClick={()=>ask('请解释这段内容',selection)}>问 Copilot</button><button onClick={()=>setSelection(null)}>清除选中</button></div>}<ReadingV2 key={`${doc.id}:${v2Edition}`} edition={v2Edition} doc={doc} restoreTop={readingPosition.current} onCite={cite} onConcept={concept} onActive={setActive} onAsk={text=>ask(text)} onSelection={setSelection} onUndo={()=>void undoPatch()} onExit={exitV2} onUnavailable={()=>{exitV2();setNotice({text:'交互讲解暂时不可用，已打开原讲解。'});}}/></>:<article className="reading-article"><div className="article-meta"><span>{doc.authors}</span><span>{doc.year}</span><span>{doc.page_count} 页</span></div><h1>{doc.title}</h1><p className="article-subtitle">{doc.subtitle}</p><div className="document-status"><span className={doc.is_demo?'status-pill':'status-pill incomplete'}><i/>{doc.is_demo?'预置教学主线':doc.status==='ready'?'完整主线':doc.status==='generating'?'分段生成中':'讲解尚未生成完成'}</span><span>{doc.is_demo?'无模型调用 · 可体验完整交互流程':'可随时回查原文'}</span></div>
            {doc.is_demo&&docId==='adaptive-search'&&<div className="argument-map"><span>沿这条线读懂</span><div><button onClick={()=>navigate('problem')}>为什么搜索</button><ArrowRight size={13}/><button onClick={()=>navigate('mechanism')}>如何缩小范围</button><ArrowRight size={13}/><button onClick={()=>navigate('limits')}>何时有效</button></div></div>}
            {selection&&<div className="selection-bar"><span>已选：{selection.slice(0,45)}{selection.length>45?'…':''}</span><button className="text-button" onClick={()=>ask('请解释这段内容',selection)}>问 Copilot<ArrowRight size={12}/></button><button className="icon-button" aria-label="清除选中内容" onClick={()=>setSelection(null)}><X size={13}/></button></div>}
            {doc.nodes.map((node,index)=><section className="reading-section" id={node.id} key={node.id}><div className="section-topline"><span className="section-index">{String(index+1).padStart(2,'0')}</span><button className="icon-button" title="针对本节提问" aria-label={`针对${node.title}提问`} onClick={()=>{setActive(node.id);ask();}}><MessageSquare size={15}/></button></div><h2>{node.title}</h2><div className="section-summary"><RichText text={node.summary}/></div>{node.kind==='steps'&&<LiveSteps node={node} step={stepStates[node.id]||0} onStep={index=>setStepStates(v=>({...v,[node.id]:index}))}/>}
              {node.kind==='live_formula'&&node.formula&&<button className="formula-block live-math" onClick={()=>{setActive(node.id);ask('请解释此公式的符号、推理与成立条件',node.formula!);}}><RichText text={'$$'+node.formula+'$$'}/><span className="formula-hint">点击公式继续提问</span></button>}
              {node.kind==='candidate_explorer'&&<Mechanism scope={scope} setScope={changeScope} previous={previous} restore={restoreScope} onAsk={()=>{setActive('mechanism');ask('为什么范围缩小会漏掉目标？');}}/>}
              {node.kind==='formula'&&<button className="formula-block" onClick={()=>{setActive('formula');ask('请逐一解释公式符号','y = Ax + ε');}}><span>y = Ax + ε</span><span className="formula-hint"><MessageSquare size={13}/>点击公式，继续追问</span></button>}
              {node.paragraphs.map((p,i)=><div className={`body-copy ${node.kind==='extracted'?'extracted-text':''}`} key={i}><RichText text={p}/></div>)}
              {node.kind==='formula'&&<details><summary>展开：从全域模型到局部模型<ChevronDown size={14}/></summary><p className="body-copy">先定义允许的坐标集合 S，再选取 A 中对应的列组成 Aₛ。约束 x 在 S 外为零，就得到 y ≈ Aₛxₛ。这里解释模型约束，不宣称已经证明唯一性或恢复误差界。</p></details>}
              {doc.visuals?.filter(v=>v.chart_or_table&&node.source_ids.some(id=>id.includes(`-p${v.page}-`))&&doc.nodes.find(n=>n.source_ids.some(id=>id.includes(`-p${v.page}-`)))?.id===node.id).map(v=><VisualFigure key={v.page} visual={v} onAsk={page=>{setActive(node.id);askRegion(page);}}/>)}{node.kind==='comparison'&&<div className="comparison-table"><div><span>搜索范围</span><span>候选数</span><span>覆盖目标</span></div><div><strong>全域</strong><span>48</span><span>是</span></div><div><strong>局部</strong><span>16</span><span>是</span></div><div><strong>极窄</strong><span>4</span><span>否</span></div></div>}
              {node.concepts.length>0&&<div className="concept-links"><span>随手查阅</span>{node.concepts.map(id=><button key={id} onClick={()=>concept(id)}><Layers3 size={12}/>{boot?.concepts[id]?.title}{boot?.library.some(i=>i.concept_id===id)&&<Check size={11}/>}<ChevronRight size={12}/></button>)}</div>}
              <div className="section-sources">{sourceButtons(node.source_ids)}</div>
              {doc.supplements.filter(p=>p.node_id===node.id).map(p=><div className="page-supplement" key={p.id} data-testid="page-supplement"><div><GitBranch size={14}/><strong>我的讲解补充</strong><span>{doc.is_demo?'来自 Copilot · 教学回答':'来自 Copilot · 千问回答'}</span></div><p>{p.text}</p><div className="supplement-footer">{sourceButtons(p.source_ids)}{doc.supplements.at(-1)?.id===p.id&&<button className="text-button" disabled={Boolean(busy)} onClick={()=>void undoPatch()}><RotateCcw size={12}/>撤回补充</button>}</div></div>)}
            </section>)}
            {!doc.nodes.length&&<div className="empty-state"><FileText size={30}/><h2>{doc.status==='generating'?'正在组织全篇讲解':'讲解尚未生成'}</h2><p>{doc.status==='generating'?'首段完成后会出现在这里。你可以先阅读原 PDF。':'本次生成没有产出可读节点。原 PDF 已保存，可阅读原文或重试。'}</p><button className="primary-button" onClick={()=>setView('original')}>阅读原 PDF</button></div>}<div className="reading-end"><CheckCheck size={23}/><h3>{doc.is_demo||doc.status==='ready'?'主线到这里，问题可以继续。':'已完成的讲解到这里，仍有缺口待处理。'}</h3><p>{doc.is_demo||doc.status==='ready'?'带着具体疑问深入，再把有用的解释留在这里。':'可以继续阅读已有内容或重试生成。'}</p><button className="secondary-button" onClick={()=>ask()}>继续问 Copilot<ArrowRight size={14}/></button></div>
          </article>}</div>}
        <footer className="reading-footer"><span><ShieldCheck size={12}/>{doc?.is_demo?'教学示例，不是论文实验复现':'原文可随时回查'}</span><button className="text-button" onClick={()=>void openChecks()}>查看原文来源<ArrowRight size={12}/></button></footer>
      </main>
      <aside id="reading-companion" className={`rightbar ${mobilePane?'is-open':''}`} aria-label="阅读伴侣"><div className="companion-heading"><span><Sparkles size={16}/>阅读伴侣</span><button className="icon-button" aria-label="收起阅读侧栏" onClick={()=>{setMobilePane(false);setRightCollapsed(true);}}><PanelRightClose size={16}/></button></div><div className="companion-tabs"><button className={pane==='knowledge'?'active':''} onClick={()=>setPane('knowledge')}><Layers3 size={14}/>知识补充</button><button className={pane==='chat'?'active':''} onClick={()=>setPane('chat')}><MessageSquare size={14}/>Copilot</button><button className={`icon-button ${pane==='library'?'active':''}`} aria-label="侧栏个人概念库" onClick={()=>setPane('library')}><BookMarked size={15}/></button></div>
        {pane==='knowledge'&&<div className="sidebar-scroll">{currentConcept?<><div className="knowledge-breadcrumb"><button className="text-button" onClick={()=>{setStack(v=>v.slice(0,-1));setShowSaved(false);}}><ArrowLeft size={13}/>{stack.length>1?'返回上层':'返回概览'}</button><span>{stack.length} 层展开</span></div><div className="concept-path">{stack.map((id,i)=><span key={id}>{i>0&&<ChevronRight size={10}/>}<button onClick={()=>{setStack(v=>v.slice(0,i+1));setShowSaved(false);}}>{boot?.concepts[id]?.title}</button></span>)}</div><h2 className="concept-title">{currentConcept.title}</h2><span className="layer-label">{LAYERS[currentConcept.layer]||currentConcept.layer}</span>{saved&&!showSaved?<div className="saved-explanation"><CheckCheck size={22}/><h3>这一层已经在你的概念库中</h3><p>默认省略重复解释。当前文档的新条件与新用法仍会保留。</p><button className="secondary-button" onClick={()=>setShowSaved(true)}>这次仍然展开</button></div>:<><p className="concept-lead">{currentConcept.lead}</p>{currentConcept.verification&&currentConcept.verification.verdict!=='supported'&&<div className="review-warning">本层解释待复核：{currentConcept.verification.issues.join('；')}</div>}<div className="body-copy"><RichText text={currentConcept.text}/></div><div className="connection"><GitBranch size={16}/><div><strong>它与当前内容的连接</strong><p>{currentConcept.why}</p></div></div></>}
          <div className="sidebar-sources">{sourceButtons(currentConcept.source_ids)}</div><button className={saved?'secondary-button full':'primary-button full'} disabled={Boolean(busy)||!conceptIsCurrent} onClick={()=>saved?void removeConcept(`${currentConcept.id}:${currentConcept.layer}`):void saveConcept(currentConcept.id)}>{saved?<Check size={15}/>:<Plus size={15}/>} {!conceptIsCurrent?'历史版本概念，仅供查阅':saved?'已加入概念库 · 点击移出':'加入个人概念库'}</button><p className="save-note">由你决定是否需要在下次阅读中重复解释。</p>{conceptIsCurrent&&!doc?.is_demo&&!currentConcept.next&&<button className="next-concept" disabled={Boolean(busy)} onClick={()=>void expandKnowledge()}><span><small>按需检索外部知识</small><strong>{busy==='expand'?'正在取证并解释…':'继续深入一层'}</strong></span><ArrowRight size={17}/></button>}{conceptIsCurrent&&currentConcept.next&&<button className="next-concept" onClick={()=>{setStack(v=>[...v,currentConcept.next!]);setShowSaved(false);}}><span><small>继续查阅相关概念</small><strong>{boot?.concepts[currentConcept.next]?.title}</strong></span><ArrowRight size={17}/></button>}<button className="secondary-button full" onClick={()=>ask(`请进一步解释${currentConcept.title}`)}>带着这个概念问 Copilot<MessageSquare size={14}/></button></>:<><div className="companion-intro"><span className="intro-symbol"><GitBranch size={25}/></span><h2>在需要的地方，<br/>多理解一层。</h2><p>查阅概念，探索它与论文的连接。<br/>你的阅读主线会留在原处。</p></div><div className="sidebar-section-label">{doc?.is_demo?'当前教学样例的概念':'当前文档的概念'}</div>{(doc?.is_demo?['candidate','sparse','matrix']:Object.keys(doc?.concepts||{})).map(id=><button className="concept-row" key={id} onClick={()=>concept(id)}><span className="concept-row-icon"><Layers3 size={16}/></span><span><strong>{boot?.concepts[id]?.title}</strong><small>{LAYERS[boot?.concepts[id]?.layer||'']}{boot?.library.some(i=>i.concept_id===id)?' · 已在概念库':''}</small></span><ChevronRight size={14}/></button>)}{!doc?.is_demo&&!Object.keys(doc?.concepts||{}).length&&<p className="muted">概念入口会随讲解逐步生成。</p>}<div className="sidebar-note"><CircleHelp size={16}/><p>这里提供随手查阅。告诉 Copilot 你具体想弄清什么，它会沿着问题继续解释。</p></div><button className="secondary-button full" onClick={()=>ask()}>从一个问题开始<ArrowRight size={14}/></button></>}</div>}
        {pane==='chat'&&<>
          <div className="chat-context"><span><Link2 size={12}/>当前：{nodeTitle(active)}</span><button className="text-button" disabled={Boolean(busy)} onClick={()=>setAttachOpen(v=>!v)}><Plus size={12}/>附加文献</button></div>
          {attachOpen&&<div className="attachment-picker"><strong>选择参考文献</strong>{boot?.documents.filter(d=>d.id!==docId).map(d=><button key={d.id} disabled={Boolean(busy)||doc?.attachments.includes(d.id)} onClick={()=>void attach(d.id)}><FileText size={13}/>{d.title}{doc?.attachments.includes(d.id)&&<Check size={13}/>}</button>)}</div>}
          {Boolean(doc?.attachments.length)&&<div className="attached-list">{doc?.attachment_documents.map(d=><span key={d.id}><Link2 size={10}/>{d.title}</span>)}</div>}
          <div className="chat-scroll">
            {!doc?.messages.length&&<div className="chat-empty"><MessageSquare size={25}/><h3>从你真正想弄清的地方开始。</h3><p>{doc?.is_demo?'当前为预设回答 Demo，可体验下面的问题。':'明确问题会直接回答；宽泛问题会先给出可调整的研究计划。'}</p>{(doc?.is_demo?['为什么范围缩小会漏掉目标？','把范围缩小演示一下','请逐一解释公式符号']:['解释这篇文档的核心论证与成立条件','请用一个例子解释当前内容','深度分析当前论证的证据与局限']).map(q=><button key={q} disabled={Boolean(busy)||Boolean(copilotRun&&!['completed','failed','cancelled'].includes(copilotRun.status))} onClick={()=>void send(q)}>{q}<ArrowRight size={12}/></button>)}</div>}
            {doc?.messages.map(message=><div className={`message ${message.role}`} key={message.id}>
              <div className="message-label">{message.role==='user'?'你':'paperMind'}{message.role==='assistant'&&<span>{message.provider==='qwen'?'千问 · 来源核验':'演示回答'}</span>}</div>
              <button className="message-anchor" onClick={()=>navigate(message.node_id)}><Link2 size={10}/>{nodeTitle(message.node_id)}</button>
              {message.selected_text&&<blockquote>{message.selected_text}</blockquote>}<div className="message-content"><RichText text={message.text}/></div>
              {message.verification&&message.verification.verdict!=='supported'&&<div className="review-warning">回答待核验：{message.verification.issues.join('；')}</div>}
              {message.role==='assistant'&&<><div className="message-sources">{sourceButtons(message.source_ids||[])}</div><div className="message-tools">{message.run_id&&<button className="text-button" onClick={()=>void toggleTimeline(message)}><GitBranch size={13}/>{timelineOpen===message.id?'收起研究过程':'查看研究过程'}</button>}{message.can_patch&&<button className="text-button" disabled={Boolean(busy)||Boolean(doc.supplements.find(p=>p.message_id===message.id))} onClick={()=>void previewMessage(message)}><Plus size={13}/>{doc.supplements.some(p=>p.message_id===message.id)?'已加入页面':'预览加入页面'}</button>}</div>{timelineOpen===message.id&&<div className="message-timeline">{messageTimelines[message.id]?<CopilotTimeline events={messageTimelines[message.id]}/>:<span><LoaderCircle size={13} className="spin"/>正在读取研究记录…</span>}</div>}</>}
            </div>)}
            {copilotRun&&<CopilotRunCard key={`${copilotRun.id}:${copilotRun.plan_revision}`} run={copilotRun} events={copilotEvents} busy={Boolean(busy)} onApprove={()=>void decideCopilot('approve_plan')} onRevise={comment=>void decideCopilot('revise_plan',comment)} onCancel={()=>void cancelCopilot()}/>} 
            {busy==='chat'&&!copilotRun&&<div className="chat-working"><LoaderCircle size={15} className="spin"/>正在保存问题…</div>}<div ref={chatEnd}/>
          </div>
          {preview&&<div className="patch-preview" data-testid="patch-preview"><div><strong>加入页面前预览</strong><button className="icon-button" aria-label="关闭修改预览" onClick={()=>setPreview(null)}><X size={14}/></button></div><p className="muted">位置：{nodeTitle(preview.node_id)}</p><p>{preview.text}</p><div className="preview-actions"><button className="secondary-button" onClick={()=>setPreview(null)}>取消</button><button className="primary-button" disabled={Boolean(busy)} onClick={()=>void applyPatch()}>确认加入</button></div></div>}
          <form className="chat-composer" onSubmit={event=>{event.preventDefault();void send();}}>
            {selectedPage&&<div className="composer-selection">针对第 {selectedPage} 页{selectedBox?'所选区域':''}<button type="button" className="icon-button" aria-label="移除页面选择" onClick={()=>{setSelectedPage(null);setSelectedBox(null);}}><X size={12}/></button></div>}
            {selection&&<div className="composer-selection">所选内容：{selection.slice(0,50)}<button type="button" className="icon-button" aria-label="移除提问内容" onClick={()=>setSelection(null)}><X size={12}/></button></div>}
            <label className="sr-only" htmlFor="question">向 Copilot 提问</label><textarea id="question" placeholder="问内容、公式，或让演示动起来…" value={question} onChange={event=>setQuestion(event.target.value)} rows={2} maxLength={6000}/>
            <div className="composer-footer"><div className="copilot-mode" role="group" aria-label="回答深度">{([['auto','自动'],['quick','快速'],['deep','深度']] as [CopilotMode,string][]).map(([value,label])=><button type="button" key={value} aria-pressed={copilotMode===value} onClick={()=>setCopilotMode(value)}>{label}</button>)}</div><button className="send-button" type="submit" aria-label="发送问题" disabled={Boolean(busy)||!question.trim()||!doc?.nodes.length||Boolean(copilotRun&&!['completed','failed','cancelled'].includes(copilotRun.status))}><Send size={15}/></button></div>
          </form>
        </>}
        {pane==='library'&&<div className="sidebar-scroll"><div className="panel-title"><BookMarked size={20}/><h2>个人概念库</h2></div><p className="muted">保存表示你选择下次跳过这一层解释，不作掌握评分。</p>{boot?.library.length?boot.library.map(item=><article className="library-entry" key={item.id}><div><h3>{item.title}</h3><button className="icon-button" aria-label={`移出${item.title}`} disabled={Boolean(busy)} onClick={()=>void removeConcept(item.id)}><Trash2 size={14}/></button></div><span className="layer-label">{LAYERS[item.layer]||item.layer} · 自行保存</span><p>{item.text}</p></article>):<div className="small-empty"><BookOpen size={25}/><p>还没有保存的概念。<br/>在知识补充中选择有用的那一层。</p><button className="text-button" onClick={()=>setPane('knowledge')}>去查阅概念<ArrowRight size={12}/></button></div>}<div className="panel-title memory-title"><Settings2 size={17}/><h3>解释偏好</h3></div><p className="muted">从对话形成，可查看依据和撤销；不改变概念库。</p>{boot?.memories.filter(m=>!m.deleted).map(m=><article className="memory-entry" key={m.id}><p>{m.text}</p><div><button className="text-button" onClick={()=>{if(m.document_id!==docId){setNotice({text:'偏好来自另一份文档，可切换文档后查看对话。'});return;}setPane('chat');window.setTimeout(()=>chatEnd.current?.scrollIntoView({block:'nearest'}),40);}}>来源对话</button><button className="text-button" disabled={Boolean(busy)} onClick={()=>void forget(m.id)}>撤销</button></div></article>)}{!boot?.memories.some(m=>!m.deleted)&&<p className="muted">暂无从对话形成的偏好。</p>}</div>}
        {pane==='sources'&&<div className="sidebar-scroll"><button className="text-button" onClick={()=>setPane('knowledge')}><ArrowLeft size={13}/>返回知识补充</button><div className="panel-title"><Link2 size={20}/><h2>引用回查</h2></div>{currentSource?<SourceEntry source={currentSource}/>:<p className="muted">选择正文中的来源查看依据。</p>}<div className="sidebar-section-label">来源账本</div>{allSources.map(s=><button key={s.id} className={`ledger-row ${s.id===selectedSource?'active':''}`} onClick={()=>setSelectedSource(s.id)}><span>{s.page}</span><strong>{s.title}</strong><ChevronRight size={12}/></button>)}</div>}
        {pane==='ledger'&&<div className="sidebar-scroll"><div className="panel-title"><Link2 size={20}/><h2>原文来源</h2></div><p className="muted">点击来源查看原句与 PDF 位置。</p>{doc?.sources.map(s=><button className="ledger-row" key={s.id} onClick={()=>cite(s.id)}><span>{s.page}</span><strong>{s.title}</strong><ChevronRight size={12}/></button>)}</div>}
      </aside>
    </div>
    {notice&&<div className="toast" role="status"><Check size={17}/><span>{notice.text}</span>{notice.memoryId&&<button disabled={Boolean(busy)} onClick={()=>void forget(notice.memoryId!)}>撤销</button>}<button aria-label="关闭提示" onClick={()=>setNotice(null)}><X size={14}/></button></div>}
    <button className="mobile-companion-button" aria-label="打开 Copilot 与知识补充" onClick={()=>setMobilePane(v=>!v)}>{mobilePane?<X size={19}/>:<MessageSquare size={19}/>}</button>
  </div>;
}
