import {useState} from 'react';
import {Check, ChevronDown, ChevronUp, CircleStop, FileSearch, LoaderCircle, PencilLine, Search, ShieldCheck, Sparkles} from 'lucide-react';
import type {CopilotEvent,CopilotRun} from './types';

const LABELS:Record<string,string>={
  turn_created:'问题已保存',plan_started:'梳理研究范围',plan_revision_requested:'修改研究计划',plan_ready:'计划准备完成',
  plan_approved:'计划已确认',research_started:'开始研究',document_retrieval_started:'检索当前论文',
  document_evidence_ready:'整理论文证据',visual_read_started:'读取原页选区',web_search_started:'检索外部资料',
  source_read:'读取来源正文',answer_composition_started:'组织回答',answer_review_started:'核验回答',
  cancel_requested:'正在停止',completed:'回答完成',cancelled:'已经停止',failed:'任务未完成',
};

function EventIcon({type,live}:{type:string;live:boolean}){
  if(live)return <LoaderCircle className="spin" size={13}/>;
  if(type.includes('search')||type.includes('retrieval')||type==='source_read')return <Search size={13}/>;
  if(type.includes('review'))return <ShieldCheck size={13}/>;
  if(type==='completed')return <Check size={13}/>;
  return <Sparkles size={13}/>;
}

export function CopilotTimeline({events,loading=false}:{events:CopilotEvent[];loading?:boolean}){
  return <div className="copilot-timeline" aria-label="Copilot 研究过程">
    {events.map((event,index)=>{
      const live=loading&&index===events.length-1&&!['completed','failed','cancelled'].includes(event.type);
      return <div className="copilot-event" key={event.event_id}><span className="copilot-event-mark"><EventIcon type={event.type} live={live}/></span><div><strong>{LABELS[event.type]||'处理问题'}</strong><p>{event.detail}</p></div></div>;
    })}
  </div>;
}

type Props={run:CopilotRun;events:CopilotEvent[];busy:boolean;onApprove:()=>void;onRevise:(comment:string)=>void;onCancel:()=>void};

export default function CopilotRunCard({run,events,busy,onApprove,onRevise,onCancel}:Props){
  const [editing,setEditing]=useState(false),[comment,setComment]=useState(''),[open,setOpen]=useState(true);
  const waiting=run.status==='awaiting_user',terminal=['completed','failed','cancelled'].includes(run.status);
  return <section className={`copilot-run-card ${waiting?'awaiting':''} ${run.status}`} aria-live="polite">
    <button className="copilot-run-heading" onClick={()=>setOpen(value=>!value)} aria-expanded={open}>
      <span className="copilot-run-symbol">{waiting?<FileSearch size={16}/>:terminal?<Check size={16}/>:<LoaderCircle className="spin" size={16}/>}</span>
      <span><small>{waiting?'需要你确认':run.mode==='deep'?'深度研究':'快速问答'}</small><strong>{waiting?'先确认研究范围':run.detail}</strong></span>
      {open?<ChevronUp size={14}/>:<ChevronDown size={14}/>} 
    </button>
    {open&&<div className="copilot-run-body">
      {waiting&&run.plan&&<div className="research-plan">
        <p>{run.plan.objective}</p>
        <ol>{run.plan.questions.map((question,index)=><li key={`${index}-${question}`}>{question}</li>)}</ol>
        <div className="research-scope"><span>当前论文</span>{run.plan.use_attached_documents&&<span>已附加文献</span>}{run.plan.use_external_sources&&<span>外部学术来源</span>}</div>
      </div>}
      {events.length>0&&<CopilotTimeline events={events} loading={!terminal&&!waiting}/>} 
      {run.error&&<p className="copilot-run-error">{run.error}</p>}
      {waiting&&editing&&<div className="plan-revision"><label htmlFor="plan-revision">希望怎样调整？</label><textarea id="plan-revision" value={comment} onChange={event=>setComment(event.target.value)} rows={3} maxLength={2000} placeholder="例如：只比较方法假设，不联网补充其他研究。"/></div>}
      {waiting&&<div className="copilot-run-actions">
        {editing?<><button className="secondary-button" onClick={()=>setEditing(false)}>返回计划</button><button className="primary-button" disabled={busy||!comment.trim()} onClick={()=>onRevise(comment)}>更新计划</button></>:<><button className="secondary-button" disabled={busy} onClick={()=>setEditing(true)}><PencilLine size={13}/>调整范围</button><button className="primary-button" disabled={busy} onClick={onApprove}><Check size={13}/>按计划开始</button></>}
      </div>}
      {!terminal&&!waiting&&<button className="stop-research" disabled={busy||run.status==='cancelling'} onClick={onCancel}><CircleStop size={14}/>{run.status==='cancelling'?'正在停止…':'停止本次任务'}</button>}
    </div>}
  </section>;
}
