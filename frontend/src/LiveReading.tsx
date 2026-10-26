import {useEffect,useRef,useState} from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {ArrowLeft,ArrowRight,MessageSquare,RotateCcw,ScanLine} from 'lucide-react';
import type {ReadingNode,Source,Visual} from './types';
import 'katex/dist/katex.min.css';

export function RichText({text}:{text:string}){
  const normalized=text.replace(/\\\(/g,'$').replace(/\\\)/g,'$').replace(/\\\[/g,'$$').replace(/\\\]/g,'$$');
  return <Markdown remarkPlugins={[remarkGfm,remarkMath]} rehypePlugins={[[rehypeKatex,{throwOnError:false,trust:false}]]} skipHtml components={{a:({children,href})=><a href={href} target="_blank" rel="noreferrer">{children}</a>,img:()=>null}}>{normalized}</Markdown>;
}

export function LiveSteps({node,step,onStep}:{node:ReadingNode;step:number;onStep:(step:number)=>void}){
  const steps=node.steps||[];if(!steps.length)return null;
  const current=steps[Math.max(0,Math.min(step,steps.length-1))];
  return <div className="live-steps"><div className="live-steps-title"><ScanLine size={16}/><strong>沿着步骤理解</strong><span>{step+1} / {steps.length}</span></div><div className="step-tabs">{steps.map((s,i)=><button key={i} aria-pressed={step===i} onClick={()=>onStep(i)}>{i+1}<span>{s.title}</span></button>)}</div><h3>{current.title}</h3><div className="body-copy"><RichText text={current.text}/></div><div className="live-step-controls"><button className="text-button" onClick={()=>onStep(Math.max(0,step-1))} disabled={step===0}><ArrowLeft size={13}/>上一步</button><button className="text-button" onClick={()=>onStep(0)}><RotateCcw size={12}/>从头看</button><button className="text-button" onClick={()=>onStep(Math.min(steps.length-1,step+1))} disabled={step===steps.length-1}>下一步<ArrowRight size={13}/></button></div></div>;
}

export function VisualFigure({visual,onAsk}:{visual:Visual;onAsk:(page:number)=>void}){
  if(!visual.chart_or_table)return null;
  return <figure className="live-figure"><a href={visual.image_url} target="_blank" rel="noreferrer"><img src={visual.image_url} alt={`原文第 ${visual.page} 页图表，点击查看完整原页`} loading="lazy"/></a><figcaption><strong>原文第 {visual.page} 页</strong><span>视觉模型读取，保留原页供核对</span></figcaption><div className="body-copy"><RichText text={visual.description}/></div>{visual.limitations.length>0&&<p className="visual-limit">识别局限：{visual.limitations.join('；')}</p>}<button className="text-button" onClick={()=>onAsk(visual.page)}><MessageSquare size={13}/>针对这页图表提问</button></figure>;
}

export function PDFRegionReader({docId,pageCount,source,onAsk}:{docId:string;pageCount:number;source?:Source;onAsk:(page:number,bbox?:number[])=>void}){
  const [page,setPage]=useState(source?.page||1),[box,setBox]=useState<number[]|null>(null),[start,setStart]=useState<number[]|null>(null);
  const area=useRef<HTMLDivElement>(null);
  useEffect(()=>{if(source?.page){setPage(source.page);setBox(null);}},[source?.id,source?.page]);
  const point=(x:number,y:number)=>{const rect=area.current!.getBoundingClientRect();return [Math.max(0,Math.min(1,(x-rect.left)/rect.width)),Math.max(0,Math.min(1,(y-rect.top)/rect.height))];};
  const highlight=box||(!start&&source?.page===page?source.bbox:null);
  return <div className="pdf-region-reader"><div className="pdf-controls"><button className="secondary-button" disabled={page===1} onClick={()=>{setPage(v=>v-1);setBox(null);}}><ArrowLeft size={13}/></button><label>第 <select aria-label="PDF 页码" value={page} onChange={e=>{setPage(Number(e.target.value));setBox(null);}}>{Array.from({length:pageCount},(_,i)=><option key={i} value={i+1}>{i+1}</option>)}</select> / {pageCount} 页</label><button className="secondary-button" disabled={page===pageCount} onClick={()=>{setPage(v=>v+1);setBox(null);}}><ArrowRight size={13}/></button><button className="primary-button" onClick={()=>onAsk(page,box||undefined)}><MessageSquare size={13}/>{box?'问所选区域':'问这一页'}</button></div><p className="muted">拖动框选图表或公式，再向 Copilot 提问。</p><div ref={area} className="pdf-page-area" onPointerDown={e=>{e.currentTarget.setPointerCapture(e.pointerId);const p=point(e.clientX,e.clientY);setStart(p);setBox(null);}} onPointerMove={e=>{if(start){const end=point(e.clientX,e.clientY);setBox([Math.min(start[0],end[0]),Math.min(start[1],end[1]),Math.max(start[0],end[0]),Math.max(start[1],end[1])]);}}} onPointerUp={()=>{setStart(null);if(box&&(box[2]-box[0]<.01||box[3]-box[1]<.01))setBox(null);}}><img key={page} src={`/api/documents/${docId}/pages/${page}/image`} alt={`原始 PDF 第 ${page} 页，可拖动框选区域`} draggable={false}/>{highlight&&<div className="pdf-selection-box" style={{left:`${highlight[0]*100}%`,top:`${highlight[1]*100}%`,width:`${(highlight[2]-highlight[0])*100}%`,height:`${(highlight[3]-highlight[1])*100}%`}}/>}</div></div>;
}
