"""Versioned PDF IR with text blocks, exact source anchors, OCR and visual inspection."""
import hashlib
import json
import re
from pathlib import Path
import pymupdf
from . import model_gateway as gateway, settings, store
from .live_contracts import Visual

PARSER_VERSION='pymupdf-qwen-v2'

def page_image(path,page,bbox=None,scale=1.3):
    with pymupdf.open(path) as pdf:
        p=pdf[page-1]
        clip=None
        if bbox:
            clip=pymupdf.Rect(bbox[0]*p.rect.width,bbox[1]*p.rect.height,bbox[2]*p.rect.width,bbox[3]*p.rect.height)
        return p.get_pixmap(matrix=pymupdf.Matrix(scale,scale),clip=clip).tobytes('png')

def parse(doc, event=lambda *a,**k:None, *, force_ocr_pages=None, inspect_visuals=True):
    path=Path(doc['file_path']);digest=hashlib.sha256(path.read_bytes()).hexdigest()
    cache=store.DATA/'parsed'/f'{digest}-{PARSER_VERSION}.json';cache.parent.mkdir(parents=True,exist_ok=True)
    previous=json.loads(cache.read_text(encoding='utf-8')) if cache.is_file() else None
    force=set(force_ocr_pages or [])
    sources=[];pages=[];gaps=[];visual_candidates=[];ocr_count=0
    with pymupdf.open(path) as pdf:
        if pdf.needs_pass:raise ValueError('PDF需要密码')
        for index,page in enumerate(pdf):
            number=index+1;raw=page.get_text('text');blocks=page.get_text('blocks',sort=True)
            text_blocks=[b for b in blocks if len(b)>6 and b[6]==0 and str(b[4]).strip()]
            drawings=len(page.get_drawings());images=len(page.get_images())
            # Heuristic column ordering; retain exact boxes so the reader can check it.
            mid=page.rect.width/2
            left=[b for b in text_blocks if b[0]<mid*.9 and b[2]<mid*1.14]
            right=[b for b in text_blocks if b[0]>mid*.9]
            two_column=len(left)>=3 and len(right)>=3
            if two_column:
                full=[b for b in text_blocks if b not in left and b not in right]
                header=[b for b in full if b[1]<max(130,page.rect.height*.16)]
                rest=[b for b in full if b not in header]
                text_blocks=sorted(header,key=lambda b:b[1])+sorted(left,key=lambda b:b[1])+sorted(right,key=lambda b:b[1])+sorted(rest,key=lambda b:b[1])
            scanned=len(raw.strip())<100 or raw.count('\ufffd')>max(10,len(raw)*.02) or number in force
            ocr_text=None;page_status='text_extracted'
            if scanned:
                old=next((p for p in (previous or {}).get('pages',[]) if p['page']==number and p.get('ocr_text')),None)
                if old and number not in force:ocr_text=old['ocr_text']
                elif ocr_count<int(settings.setting('PAPERMIND_OCR_PAGE_BUDGET','30')):
                    event('ocr',f'识别第 {number} 页')
                    try:
                        ocr_text=gateway.ocr(page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).tobytes('png'),context={'document_id':doc['id'],'page':number})
                        ocr_count+=1
                    except Exception as error:gaps.append({'page':number,'reason':'OCR失败：'+settings.sanitize(error)})
                else:gaps.append({'page':number,'reason':'超出本次OCR页预算，可提高预算后继续'})
                if ocr_text:
                    text_blocks=[(0,0,page.rect.width,page.rect.height,ocr_text,0,0)];page_status='ocr_extracted'
                elif len(raw.strip())<100:
                    page_status='unresolved'
            block_ids=[]
            for bi,b in enumerate(text_blocks):
                text=str(b[4]).strip()
                if len(text)<8:continue
                sid=f'{doc["id"]}-p{number}-b{bi}'
                bbox=[round(max(0,min(1,b[j]/(page.rect.width if j%2==0 else page.rect.height))),5) for j in range(4)]
                sources.append({'id':sid,'kind':'paper','title':f'{doc["title"]} · 第 {number} 页','page':number,'quote':text,'locator':f'物理页 {number}，文字块 {bi}'+('，OCR识别（待对照原页）' if ocr_text else ''),'status':'ocr_extracted' if ocr_text else 'located','url':None,'bbox':bbox,'file_hash':digest,'quote_hash':hashlib.sha256(text.encode()).hexdigest(),'parser_version':PARSER_VERSION})
                block_ids.append(sid)
            body='\n'.join(str(b[4]).strip() for b in text_blocks)
            pages.append({'page':number,'text':body,'source_ids':block_ids,'status':page_status,'ocr_text':ocr_text,'two_column_heuristic':two_column,'images':images,'vector_paths':drawings})
            if images or drawings>12 or re.search(r'(Fig(?:ure)?\.?\s*[1-9]|Table\s*[1-9]|图\s*[一二三四五123456789]|表\s*[一二三四五123456789])',raw):
                visual_candidates.append((number,images+min(drawings,80)/10))
    visuals=[]
    if inspect_visuals:
        candidates=sorted(visual_candidates,key=lambda x:x[1],reverse=True)[:int(settings.setting('PAPERMIND_VISUAL_PAGE_BUDGET','2'))]
        for number,_ in sorted(candidates):
            event('vision',f'读取第 {number} 页图表与公式')
            cached=next((v for v in (previous or {}).get('visuals',[]) if v['page']==number),None)
            if cached:visuals.append(cached);continue
            prompt=('只输出JSON。读取这张论文原页，描述图表含义与可辨认公式。不要编造模糊数据；'
                    'extracted_data只列清晰读到的标签/数值，limitations说明不能读到的内容。'
                    'page必须为'+str(number)+'。JSON Schema:'+json.dumps(Visual.model_json_schema(),ensure_ascii=False))
            try:
                value=Visual.model_validate(gateway.request('vision',gateway.image_message(page_image(path,number),prompt),max_tokens=3000,context={'document_id':doc['id'],'page':number})).model_dump()
                value['image_url']=f'/api/documents/{doc["id"]}/pages/{number}/image'
                value['source_ids']=pages[number-1]['source_ids']
                value['status']='model_observation'
                visuals.append(value)
            except Exception as error:
                visuals.append({'page':number,'description':'图表视觉读取失败','chart_or_table':True,'formulas':[],'extracted_data':[],'limitations':[settings.sanitize(error)],'source_ids':pages[number-1]['source_ids'],'image_url':f'/api/documents/{doc["id"]}/pages/{number}/image','status':'unresolved'})
    result={'parser_version':PARSER_VERSION,'file_hash':digest,'pages':pages,'sources':sources,'visuals':visuals,'gaps':gaps,'page_count':len(pages),'ocr_pages':sum(p['status']=='ocr_extracted' for p in pages),'two_column_pages':sum(p['two_column_heuristic'] for p in pages)}
    cache.write_text(store.encode(result),encoding='utf-8')
    return result

def load_ir(doc):
    path=doc.get('ir_path')
    return json.loads(Path(path).read_text(encoding='utf-8')) if path and Path(path).is_file() else None
