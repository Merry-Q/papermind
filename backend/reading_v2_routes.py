"""Generated whole-document pages are immediately available to the reader."""
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from . import reading_v2 as reading

router=APIRouter(prefix='/api',tags=['reading-v2'])

@router.post('/documents/{did}/reading-v2',status_code=202)
def generate(did:str):
    try:return reading.enqueue(did)
    except ValueError as e:raise HTTPException(422,str(e))


@router.get('/documents/{did}/reading-v2/default')
def default(did:str):
    return reading.default_edition(did)


@router.post('/documents/{did}/reading-v2/{eid}/cancel')
def cancel(did:str,eid:str):
    try:return reading.cancel(eid,did)
    except ValueError as e:raise HTTPException(404,str(e))


@router.get('/documents/{did}/reading-v2/{eid}')
def metadata(did:str,eid:str,inspection:bool=False):
    try:
        item,artifact,_=reading.load_completed(eid,did)
        return {'id':eid,'document_id':did,'status':item['status'],'title':artifact['title'],'description':artifact['description'],'limitations':artifact['limitations']}
    except (ValueError,OSError) as e:raise HTTPException(409,str(e))

@router.get('/documents/{did}/reading-v2/{eid}/artifact')
def artifact(did:str,eid:str,channel:str=Query(min_length=8,max_length=100),inspection:bool=False):
    try:
        item,artifact,data=reading.load_completed(eid,did)
        return {'html':reading.frame_html(artifact,data,item,channel)}
    except (ValueError,OSError) as e:raise HTTPException(409,str(e))

@router.get('/documents/{did}/reading-v2/{eid}/export',response_class=HTMLResponse)
def export(did:str,eid:str):
    try:
        item,artifact,data=reading.load_completed(eid,did)
        return HTMLResponse(reading.frame_html(artifact,data,item,'standalone-export'),headers={'Content-Disposition':'attachment; filename="papermind-reading.html"'})
    except (ValueError,OSError) as e:raise HTTPException(409,str(e))
