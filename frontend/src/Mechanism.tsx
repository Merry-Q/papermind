import { ArrowDownRight, Check, Crosshair, RotateCcw, ScanLine } from 'lucide-react';
import type { Scope } from './types';

const counts = {all:48,local:16,narrow:4};
export default function Mechanism({scope,setScope,previous,restore,onAsk}:{scope:Scope;setScope:(s:Scope)=>void;previous:Scope|null;restore:()=>void;onAsk:()=>void}) {
  const covered = scope !== 'narrow';
  return <div className="explorer" data-testid="mechanism">
    <div className="explorer-heading"><div><ScanLine size={17}/><strong>搜索范围实验室</strong></div><span>教学演示 · 合成数据</span></div>
    <div className="scope-control" role="group" aria-label="选择搜索范围">{(['all','local','narrow'] as Scope[]).map((s,i)=><button key={s} aria-pressed={scope===s} onClick={()=>setScope(s)}>{['全域搜索','局部搜索','极窄范围'][i]}</button>)}</div>
    <div className="experiment-body">
      <div className="grid-wrap"><div className="grid-axis"><span>候选位置</span><span>8 × 6</span></div><div className="candidate-grid" role="img" aria-label={`${counts[scope]} 个候选位置，${covered?'覆盖':'未覆盖'}真实目标`}>{Array.from({length:48},(_,index)=>{
        const col=index%8,row=Math.floor(index/8),target=index===21;
        const active=scope==='all'||(scope==='local'&&col>=3&&col<=6&&row>=1&&row<=4)||(scope==='narrow'&&col>=3&&col<=4&&row>=2&&row<=3);
        return <div key={index} className={`grid-cell ${active?'included':''} ${target?'target':''}`}>{target?<Crosshair size={23}/>:<i/>}</div>;
      })}</div><div className="grid-legend"><span><i className="dot active"/>搜索范围</span><span><Crosshair size={13}/>真实目标</span></div></div>
      <div className="experiment-readout"><span>当前候选</span><strong data-testid="candidate-count">{counts[scope]}<small>/ 48</small></strong><div className={`coverage ${covered?'good':'miss'}`}>{covered?<Check size={15}/>:<ArrowDownRight size={15}/>}<span>{covered?'真实目标仍在范围内':'真实目标被排除'}</span></div><p>{covered?'候选减少不代表精度提高。下一步仍取决于观测和求解条件。':'计算范围更小，但正确位置已经不在允许的答案中。'}</p></div>
    </div>
    <div className="explorer-footer"><button className="text-button" onClick={restore} disabled={!previous}><RotateCcw size={13}/>恢复上一步</button><button className="text-button" onClick={onAsk}>为什么会这样？<ArrowDownRight size={14}/></button></div>
  </div>;
}
