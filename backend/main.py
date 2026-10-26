"""paperMind local Qwen reading API. Start: python -m uvicorn backend.main:app."""
import hashlib
import json
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import pymupdf
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from . import store
from .contracts import AttachmentRequest, ChatRequest, ConceptRequest, PatchRequest, RevisionRequest
from .copilot import reply
from .demo_data import CONCEPTS
from . import copilot_runs, jobs, live_copilot, settings
from .live_routes import router as live_router
from .reading_v2_routes import router as reading_v2_router
from . import reading_v2

@asynccontextmanager
async def lifespan(_app):
    store.initialize()
    copilot_runs.startup()
    reading_v2.startup()
    if settings.live_enabled():jobs.startup()
    yield
    jobs.shutdown()
    copilot_runs.shutdown()
    reading_v2.shutdown()

app = FastAPI(title="paperMind local", version="0.2.0", lifespan=lifespan)

def require_doc(db, doc_id):
    doc = store.get_document(db, doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return doc

def require_revision(doc, revision):
    if doc["revision"] != revision:
        raise HTTPException(409, "页面已更新，请刷新后重新预览修改")

def require_node(doc, node_id):
    if node_id=='document' and not doc['is_demo']:return
    if not any(n["id"] == node_id for n in doc["nodes"]):
        raise HTTPException(422, "提问位置不属于当前文档")

def history(db, doc_id):
    return [json.loads(r[0]) for r in db.execute("SELECT payload FROM messages WHERE document_id=? ORDER BY rowid", (doc_id,))]

def save_message(db, doc_id, message):
    db.execute("INSERT INTO messages(id,document_id,role,payload) VALUES (?,?,?,?)", (message["id"], doc_id, message["role"], store.encode(message)))

@app.get("/api/health")
def health():
    return {"status":"ok","mode":"live" if settings.live_enabled() else "unconfigured","model_provider":"qwen" if settings.live_enabled() else "fixture","credential_configured":bool(settings.api_key()),"llm_connected":settings.live_enabled(),"connection_note":"凭证已配置；真实调用结果见运行记录","models":settings.models() if settings.live_enabled() else {}}

@app.get("/api/bootstrap")
def bootstrap():
    with store.connection() as db:
        docs = [{k: d[k] for k in ["id", "title", "is_demo", "status", "type"]} for d in store.items(db, "documents")]
        concepts={};concept_sources=[]
        for value in store.items(db,'documents'):
            current_concepts=CONCEPTS if value['is_demo'] else value.get('concepts',{})
            concepts.update(current_concepts)
            refs={sid for c in current_concepts.values() for sid in c['source_ids']}
            concept_sources.extend(s for s in value['sources'] if s['id'] in refs)
        return {"documents": docs, "concepts": concepts, "concept_sources": concept_sources, "library": store.items(db, "library"), "memories": store.items(db, "memories"),"default_document_id":reading_v2.default_document()}

@app.get("/api/documents/{doc_id}")
def document(doc_id: str):
    with store.connection() as db:
        doc = require_doc(db, doc_id)
        public = {**doc, "file_path": None, 'ir_path':None, "has_pdf": bool(doc["file_path"])}
        public["messages"] = history(db, doc_id)
        public["patches"] = [json.loads(r[0]) for r in db.execute("SELECT payload FROM patches WHERE document_id=? ORDER BY rowid", (doc_id,))]
        public["attachment_documents"] = [{"id": d["id"], "title": d["title"]} for key in doc["attachments"] if (d := store.get_document(db, key))]
        public["attachment_sources"] = [s for key in doc["attachments"] if (d := store.get_document(db, key)) for s in d["sources"]]
        public['job']=jobs.latest_job(db,doc_id)
        public['reading_job']=reading_v2.latest(doc_id)
        public['canonical_complete']=doc.get('canonical_complete',doc['status']=='ready')
        return public

@app.post("/api/documents", status_code=201)
def upload(file: UploadFile):
    # Synchronous route runs in FastAPI's threadpool; bound actual bytes, not Content-Length.
    raw = file.file.read(20 * 1024 * 1024 + 1)
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(413, "PDF 超过 20 MB，请先拆分文档")
    if not raw.startswith(b"%PDF-"):
        raise HTTPException(415, "请选择有效的 PDF 文件")
    try:
        with pymupdf.open(stream=raw, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise HTTPException(422, "PDF 已加密，请先移除密码")
            if pdf.page_count > 120:
                raise HTTPException(422, "当前最多处理 120 页，请先拆分文档")
            pages = [p.get_text("text")[:20000] for p in pdf]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, "PDF 无法解析，请检查文件是否损坏")
    digest = hashlib.sha256(raw).hexdigest()
    doc_id = "pdf-" + digest[:16]
    sources = [{"id": f"{doc_id}-p{i+1}", "kind": "paper", "title": f"上传 PDF · 第 {i+1} 页", "page": i+1, "quote": text[:1400] or "此页未提取到文本，可能需要 OCR。", "locator": "本地文本抽取，未核验公式与阅读顺序", "status": "unverified", "url": None} for i, text in enumerate(pages)]
    with store.connection(write=True) as db:
        existing = store.get_document(db, doc_id)
        if existing:
            return {"id": doc_id, "status": existing["status"], "deduplicated": True}
        upload_dir = store.DATA / "uploads"
        upload_dir.mkdir(exist_ok=True)
        path = upload_dir / f"{digest}.pdf"
        path.write_bytes(raw)
        doc = {"id": doc_id, "title": Path(file.filename or "上传文档.pdf").stem[:150], "subtitle": "文本已抽取，完整讲解尚未生成", "authors": "本地上传", "year": "", "type": "PDF", "is_demo": False, "status": "incomplete", "revision": 1, "page_count": len(pages), "file_path": str(path), "sources": sources, "nodes": [{"id": "extracted", "title": "可读草稿：原文抽取", "summary": "以下为生成前的原文抽取草稿，完整讲解需要模型任务完成。公式、图表及阅读顺序尚未核验。", "paragraphs": [(p[:3000] or "未提取到文本，请查看原 PDF。") for p in pages[:5]], "source_ids": [s["id"] for s in sources[:5]], "concepts": [], "kind": "extracted", "status": "incomplete"}], "supplements": [], "attachments": []}
        store.put_document(db, doc)
    job=jobs.enqueue(doc_id) if settings.live_enabled() else None
    return {"id": doc_id, "status": "generating" if job else "incomplete", "deduplicated": False,'job':job}

def get_pdf_path(doc_id):
    with store.connection() as db:
        doc = require_doc(db, doc_id)
        path = Path(doc["file_path"]) if doc["file_path"] else None
        if not path or not path.is_file() or not path.resolve().is_relative_to(store.DATA):
            raise HTTPException(404, "教学样例只有来源摘录；上传的 PDF 才有原文件")
        return path

@app.get("/api/documents/{doc_id}/file")
def pdf_file(doc_id: str):
    return FileResponse(get_pdf_path(doc_id), media_type="application/pdf", headers={"Content-Disposition": "inline"})

@app.get("/api/documents/{doc_id}/pages/{page}/image")
def pdf_page(doc_id: str, page: int):
    with pymupdf.open(get_pdf_path(doc_id)) as pdf:
        if not 1 <= page <= len(pdf):
            raise HTTPException(404, "页码不存在")
        pix = pdf[page-1].get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2))
        return Response(pix.tobytes("png"), media_type="image/png")

@app.post("/api/documents/{doc_id}/messages", status_code=201)
def chat(doc_id: str, body: ChatRequest):
    if not body.text.strip():
        raise HTTPException(422, "请输入问题")
    if body.bbox and (not body.selected_page or not (0<=body.bbox[0]<body.bbox[2]<=1 and 0<=body.bbox[1]<body.bbox[3]<=1)):
        raise HTTPException(422,'框选区域必须是有效的页内归一化坐标')
    with store.connection() as db:
        doc = require_doc(db, doc_id)
        require_node(doc, body.node_id)
        previous=history(db,doc_id)
    external=[]
    if doc['is_demo']:
        answer = reply(doc, body.text)
    elif settings.live_enabled():
        try:answer,external=live_copilot.answer(doc,body,previous)
        except Exception as e:raise HTTPException(502,settings.sanitize(e))
    else:
        answer=reply(doc,body.text)
    user = {"id": str(uuid4()), "role": "user", "text": body.text.strip(), "node_id": body.node_id, "selected_text": body.selected_text,'selected_page':body.selected_page,'bbox':body.bbox}
    assistant = {"id": str(uuid4()), "role": "assistant", "node_id": body.node_id, **answer}
    with store.connection(write=True) as db:
        current=require_doc(db,doc_id)
        if external:
            known={s['id'] for s in current['sources']}
            current['sources'].extend(s for s in external if s['id'] not in known)
            store.put_document(db,current)
        new_memory = None
        if answer["memory"]:
            candidate = {**answer["memory"], "document_id": doc_id, "message_id": user["id"]}
            # Deletion is a tombstone: undo does not make the next turn recreate the same inference.
            row = db.execute("SELECT id FROM memories WHERE id=?", (candidate["id"],)).fetchone()
            if not row:
                new_memory = {**candidate, "deleted": False}
                db.execute("INSERT INTO memories VALUES (?,?)", (new_memory["id"], store.encode(new_memory)))
        save_message(db, doc_id, user)
        save_message(db, doc_id, assistant)
    return {"user": user, "assistant": assistant, "new_memory": new_memory}

@app.post("/api/documents/{doc_id}/attachments")
def attach(doc_id: str, body: AttachmentRequest):
    with store.connection(write=True) as db:
        doc = require_doc(db, doc_id)
        require_doc(db, body.document_id)
        if doc_id == body.document_id:
            raise HTTPException(422, "不能附加当前文档自身")
        if body.document_id not in doc["attachments"]:
            doc["attachments"].append(body.document_id)
            store.put_document(db, doc)
    return {"attachments": doc["attachments"]}

@app.post("/api/documents/{doc_id}/patches", status_code=201)
def preview_patch(doc_id: str, body: PatchRequest):
    with store.connection(write=True) as db:
        doc = require_doc(db, doc_id)
        require_revision(doc, body.base_revision)
        row = db.execute("SELECT payload FROM messages WHERE id=? AND document_id=? AND role='assistant'", (body.message_id, doc_id)).fetchone()
        if not row:
            raise HTTPException(404, "找不到可加入页面的回答")
        message = json.loads(row[0])
        if not message["can_patch"]:
            raise HTTPException(422, "当前回答不适合作为页面补充")
        if any(s["message_id"] == body.message_id for s in doc["supplements"]):
            raise HTTPException(409, "该回答已经加入页面")
        patch = {"id": str(uuid4()), "document_id": doc_id, "node_id": message["node_id"], "text": message["text"], "source_ids": message["source_ids"], "message_id": message["id"], "base_revision": body.base_revision, "status": "preview"}
        db.execute("INSERT INTO patches VALUES (?,?,?)", (patch["id"], doc_id, store.encode(patch)))
    return patch

@app.post("/api/documents/{doc_id}/patches/{patch_id}/{operation}")
def mutate_patch(doc_id: str, patch_id: str, operation: str, body: RevisionRequest):
    if operation not in {"apply", "undo"}:
        raise HTTPException(404, "未知修改操作")
    with store.connection(write=True) as db:
        doc = require_doc(db, doc_id)
        require_revision(doc, body.base_revision)
        row = db.execute("SELECT payload FROM patches WHERE id=? AND document_id=?", (patch_id, doc_id)).fetchone()
        if not row:
            raise HTTPException(404, "修改不存在")
        patch = json.loads(row[0])
        if operation == "apply":
            if patch["status"] != "preview" or patch["base_revision"] != doc["revision"]:
                raise HTTPException(409, "预览已过期，请重新生成预览")
            if any(s["message_id"] == patch["message_id"] for s in doc["supplements"]):
                raise HTTPException(409, "该回答已经加入页面")
            doc["supplements"].append({k: patch[k] for k in ["id", "node_id", "text", "source_ids", "message_id"]})
            patch["status"] = "applied"
        else:
            if patch["status"] != "applied" or not doc["supplements"] or doc["supplements"][-1]["id"] != patch_id:
                raise HTTPException(409, "请先撤回最近一次页面补充")
            doc["supplements"].pop()
            patch["status"] = "undone"
        doc["revision"] += 1
        store.put_document(db, doc)
        db.execute("UPDATE patches SET payload=? WHERE id=?", (store.encode(patch), patch_id))
    return {"revision": doc["revision"], "patch": patch}

@app.put("/api/library")
def save_concept(body: ConceptRequest):
    with store.connection(write=True) as db:
        doc = require_doc(db, body.document_id)
        concept=(CONCEPTS if doc['is_demo'] else doc.get('concepts',{})).get(body.concept_id)
        if not concept:raise HTTPException(422,'该概念不属于当前文档')
        item_id=f'{concept["id"]}:{concept["layer"]}'
        item = {"id": item_id, "concept_id": concept["id"], "layer": concept["layer"], "title": concept["title"], "text": concept["text"], "document_id": doc["id"], "declaration": "self_reported", "source_ids": concept["source_ids"],'domain':concept.get('domain'),'verification':concept.get('verification')}
        db.execute("INSERT INTO library VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (item_id, store.encode(item)))
    return item

@app.delete("/api/library/{item_id:path}")
def remove_concept(item_id: str):
    with store.connection(write=True) as db:
        db.execute("DELETE FROM library WHERE id=?", (item_id,))
    return {"deleted": True}

@app.delete("/api/memories/{memory_id}")
def remove_memory(memory_id: str):
    with store.connection(write=True) as db:
        row = db.execute("SELECT payload FROM memories WHERE id=?", (memory_id,)).fetchone()
        if row:
            memory = {**json.loads(row[0]), "deleted": True}
            db.execute("UPDATE memories SET payload=? WHERE id=?", (store.encode(memory), memory_id))
    return {"deleted": True}

DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
app.include_router(live_router)
app.include_router(reading_v2_router)
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="web")
