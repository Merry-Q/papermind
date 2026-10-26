import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {api} from './api';
import type {Document} from './types';
import './reading-v2.css';

type Props={edition:string;doc:Document;restoreTop:number;onCite:(id:string)=>void;onConcept:(id:string)=>void;onActive:(id:string)=>void;onAsk:(text:string)=>void;onSelection:(text:string)=>void;onUndo:()=>void;onExit:()=>void;onUnavailable?:()=>void};
type Meta={title:string;description:string;status:string};
export default function ReadingV2(props:Props){
 const {edition,doc}=props;
 const frame=useRef<HTMLIFrameElement>(null),callbacks=useRef(props);
 const initialTop=useRef(props.restoreTop),restored=useRef(false);
 callbacks.current=props;
 const [channel]=useState(()=>crypto.randomUUID()),[html,setHtml]=useState(''),[meta,setMeta]=useState<Meta|null>(null),[height,setHeight]=useState(1200),[error,setError]=useState(''),[ready,setReady]=useState(false),[measured,setMeasured]=useState(false),[positionRestored,setPositionRestored]=useState(false);
 const inspection=new URLSearchParams(location.search).get('readingInspection')==='1';
 const base=`/documents/${doc.id}/reading-v2/${edition}`;
 const send=(type:string,payload:Record<string,unknown>={})=>frame.current?.contentWindow?.postMessage({type,channel,...payload},'*');
 useLayoutEffect(()=>{const scroller=frame.current?.closest('.reading-scroll');if(!ready||!measured||restored.current||!scroller)return;scroller.scrollTop=Math.min(initialTop.current,Math.max(0,scroller.scrollHeight-scroller.clientHeight));restored.current=true;setPositionRestored(true);},[ready,height,measured]);
 useEffect(()=>{
  const controller=new AbortController();setHtml('');setReady(false);setError('');
  Promise.all([api<Meta>(`${base}?inspection=${inspection}`,{signal:controller.signal}),api<{html:string}>(`${base}/artifact?channel=${channel}&inspection=${inspection}`,{signal:controller.signal})]).then(([m,a])=>{setMeta(m);setHtml(a.html);}).catch(e=>{if(e.name!=='AbortError')setError(e.message);});
  return()=>controller.abort();
 },[base,channel,inspection]);
 useEffect(()=>{
  let messages=0,windowStart=performance.now();
  const receive=(event:MessageEvent)=>{
   const d=event.data;
   if(event.source!==frame.current?.contentWindow||!d||d.channel!==channel||d.edition!==edition||d.document!==doc.id||typeof d.type!=='string')return;
   const time=performance.now();if(time-windowStart>1000){windowStart=time;messages=0;}if(++messages>100)return;
   const cb=callbacks.current,node=typeof d.node==='string'&&cb.doc.nodes.some(n=>n.id===d.node)?d.node:null;
   if(d.type==='resize'&&Number.isFinite(d.height)&&d.height>=100&&d.height<=100000){setHeight(Math.ceil(d.height));setMeasured(true);}
   else if(d.type==='ready')setReady(true);
   else if(d.type==='error')setError('这份交互讲解运行中断，请恢复原讲解后继续阅读。');
   else if(d.type==='cite'&&cb.doc.sources.some(s=>s.id===d.id))cb.onCite(d.id);
   else if(d.type==='concept'&&cb.doc.concepts?.[d.id]){if(node)cb.onActive(node);cb.onConcept(d.id);}
   else if(d.type==='active'&&node)cb.onActive(node);
   else if((d.type==='ask'||d.type==='selection')&&node&&typeof d.text==='string'&&d.text.length>=4&&d.text.length<=2000){cb.onActive(node);if(d.type==='ask')cb.onAsk(d.text);else cb.onSelection(d.text);}
   else if(d.type==='scroll'&&Number.isFinite(d.top)&&d.top>=0&&d.top<=100000){const scroller=frame.current?.closest('.reading-scroll');if(scroller&&frame.current){const toolbar=frame.current.parentElement?.querySelector('.reading-v2-tools')?.getBoundingClientRect().height||0;scroller.scrollTo({top:scroller.scrollTop+frame.current.getBoundingClientRect().top-scroller.getBoundingClientRect().top+d.top-toolbar-20,behavior:'instant'});}}
   else if(d.type==='undo'&&cb.doc.supplements.at(-1)?.id===d.id)cb.onUndo();
  };
  window.addEventListener('message',receive);return()=>window.removeEventListener('message',receive);
 },[channel,edition,doc.id]);
 useEffect(()=>{
  if(!ready)return;
  send('supplements',{items:doc.supplements.map(p=>({...p,can_undo:doc.supplements.at(-1)?.id===p.id}))});
 },[ready,doc.supplements]);
 useEffect(()=>{
  if(!ready)return;
  const scroller=frame.current?.closest('.reading-scroll');
  const viewport=()=>{if(frame.current&&scroller)send('viewport',{top:Math.max(0,scroller.getBoundingClientRect().top-frame.current.getBoundingClientRect().top)});};
  const navigate=(event:Event)=>{const id=(event as CustomEvent<{id:string}>).detail?.id;if(callbacks.current.doc.nodes.some(n=>n.id===id))send('navigate',{node:id});};
  scroller?.addEventListener('scroll',viewport,{passive:true});window.addEventListener('resize',viewport);window.addEventListener('papermind-v2-navigate',navigate);viewport();
  return()=>{scroller?.removeEventListener('scroll',viewport);window.removeEventListener('resize',viewport);window.removeEventListener('papermind-v2-navigate',navigate);};
 },[ready,channel]);
 useEffect(()=>{if(!html||ready)return;const t=setTimeout(()=>setError('交互讲解未能打开，可以恢复原讲解继续阅读。'),20000);return()=>clearTimeout(t);},[html,ready]);
 useEffect(()=>{if(error)callbacks.current.onUnavailable?.();},[error]);
 return <div className="reading-v2" data-edition={edition} data-reading-ready={ready&&positionRestored}>
  <div className="reading-v2-tools"><span>{meta?.title?'整篇交互讲解':'交互讲解'}</span><button disabled={!ready||!positionRestored} onClick={props.onExit}>恢复原讲解</button>{meta&&<a href={`/api${base}/export`} download>保存独立网页</a>}</div>
  {error?<div className="reading-v2-error" role="alert"><p>{error}</p><button onClick={props.onExit}>恢复原讲解</button></div>:html?<iframe ref={frame} title="论文交互讲解" sandbox="allow-scripts" srcDoc={html} style={{height}}/>:<p className="reading-v2-loading" role="status">正在打开完整交互讲解…</p>}
 </div>;
}
