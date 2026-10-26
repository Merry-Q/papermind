"""Download a version-pinned, public PDF corpus and inspect observable PDF properties.

Run: python scripts/prepare_corpus.py [--refresh]
No model, OCR, academic-validation or application database calls are made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "test-corpus"
MANIFEST = ROOT / "tests" / "corpus" / "manifest.json"
MAX_BYTES = 50 * 1024 * 1024
MAX_PAGES = 250

PAPERS = [
    dict(id="attention", title="Attention Is All You Need", authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Łukasz Kaiser", "Illia Polosukhin"], year=2017, domain="AI", language="en", original_url="https://arxiv.org/abs/1706.03762", download_urls=["https://arxiv.org/pdf/1706.03762v7"], version="arXiv v7", boundaries=["双栏阅读顺序", "注意力公式/矩阵维度", "BLEU表格与训练设置", "机制演示不冒充训练复现"]),
    dict(id="rag", title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", authors=["Patrick Lewis", "Ethan Perez", "Aleksandra Piktus", "Fabio Petroni", "Vladimir Karpukhin", "Naman Goyal", "Heinrich Küttler", "Mike Lewis", "Wen-tau Yih", "Tim Rocktäschel", "Sebastian Riedel", "Douwe Kiela"], year=2020, domain="AI", language="en", original_url="https://arxiv.org/abs/2005.11401", download_urls=["https://arxiv.org/pdf/2005.11401v4"], version="arXiv v4", boundaries=["概率分解与检索生成关系", "主文与附录区分", "跨论文概念复用", "检索准确不等于生成事实正确"]),
    dict(id="adaptive-dcs-somp", title="Adaptive DCS-SOMP for Localization Parameter Estimation in 5G Networks", authors=["Paulo Francisco da Conceição", "Flávio Geraldo Coelho Rocha"], year=2023, domain="通信", language="en", original_url="https://www.mdpi.com/1424-8220/23/22/9073", download_urls=["https://mdpi-res.com/d_attachment/sensors/sensors-23-09073/article_deploy/sensors-23-09073-v2.pdf", "https://www.mdpi.com/1424-8220/23/22/9073/pdf"], version="publisher v2 if available; actual download_url and hash authoritative", boundaries=["稀疏恢复与通信前置知识", "多层公式和符号", "仿真曲线不等于真实部署", "搜索域教学模型的边界"]),
    dict(id="shannon", title="A Mathematical Theory of Communication", authors=["Claude E. Shannon"], year=1948, domain="通信", language="en", original_url="https://doi.org/10.1002/j.1538-7305.1948.tb01338.x", download_urls=["https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf"], version="Harvard institutional reprint with corrections, combines July/October 1948 installments", boundaries=["长理论文档覆盖", "定理与条件不可省略", "熵公式与示意图", "历史语境与后续知识分开"]),
    dict(id="lyrics", title="Decoding the Style and Bias of Song Lyrics", authors=["Manash Pratim Barman", "Amit Awekar", "Sambhav Kothari"], year=2019, domain="人文社科", language="en", original_url="https://arxiv.org/abs/1907.07818", download_urls=["https://arxiv.org/pdf/1907.07818v1"], version="arXiv v1", boundaries=["数字人文与文化语料", "WEAT偏差指标", "表格统计不能替代社会因果结论", "短文完整论证"]),
    dict(id="moral-machine", title="The Moral Machine experiment", authors=["Edmond Awad", "Sohan Dsouza", "Richard Kim", "Jonathan Schulz", "Joseph Henrich", "Azim Shariff", "Jean-François Bonnefon", "Iyad Rahwan"], year=2018, domain="哲学/实验伦理/人文社科", language="en", original_url="https://dspace.mit.edu/entities/publication/c5779012-d165-4644-b276-76ab3365ca26", download_urls=["https://dspace.mit.edu/bitstreams/750c4524-46a2-4013-916a-c8131d726b56/download", "https://dspace.mit.edu/server/api/core/bitstreams/750c4524-46a2-4013-916a-c8131d726b56/content", "https://dspace.mit.edu/bitstream/handle/1721.1/125065/Moral%20Machine%20Paper.pdf"], version="MIT author final manuscript; not publisher layout", boundaries=["图示情景与偏好统计", "描述性伦理不等于规范性结论", "文化聚类与样本选择", "人数/决策次数/地域单位区别"]),
    dict(id="simulation-argument", title="Are You Living in a Computer Simulation?", authors=["Nick Bostrom"], year=2003, domain="哲学", language="en", original_url="https://simulation-argument.com/", download_urls=["https://simulation-argument.com/simulation.pdf", "http://simulation-argument.com/simulation.pdf"], version="author-hosted paper published in Philosophical Quarterly 53(211):243–255", boundaries=["纯理论哲学论证结构", "三分命题不能误写成已证实生活在模拟中", "概率公式的前提", "没有实证图表时不得强造数值演示"]),
    dict(id="generative-ai-work", title="Generative AI at Work", authors=["Erik Brynjolfsson", "Danielle Li", "Lindsey R. Raymond"], year=2023, domain="经济", language="en", original_url="https://www.nber.org/papers/w31161", download_urls=["https://www.nber.org/system/files/working_papers/w31161/w31161.pdf", "https://arxiv.org/pdf/2304.11771v1"], version="NBER working paper or arXiv 2304.11771 v1 fallback; actual download_url authoritative; not 2025 QJE version", boundaries=["长实证论文与附录", "样本人数版本差异5179/5172", "平均效果与异质性", "相关性/因果识别与外推边界"]),
    dict(id="macroeconomics-ai", title="The Simple Macroeconomics of AI", authors=["Daron Acemoglu"], year=2024, domain="经济", language="en", original_url="https://www.nber.org/papers/w32487", download_urls=["https://www.nber.org/system/files/working_papers/w32487/w32487.pdf", "https://economics.mit.edu/sites/default/files/2024-05/The%20Simple%20Macroeconomics%20of%20AI.pdf", "https://shapingwork.mit.edu/wp-content/uploads/2024/05/Acemoglu_Macroeconomics-of-AI_May-2024.pdf"], version="NBER working paper or May 12 2024 MIT author-hosted fallback; actual download_url authoritative", boundaries=["长理论加数据校准", "模型假设与预测区间", "GDP与TFP及时间尺度", "与微观生产率研究比较不能直接等同"]),
    dict(id="cnnic55", title="第55次中国互联网络发展状况统计报告", authors=["中国互联网络信息中心（CNNIC）"], year=2025, domain="人文社科/经济研报", language="zh", original_url="https://www.cnnic.cn/n4/2025/0117/c88-11229.html", download_urls=["https://www.cnnic.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf", "https://www.cnnic.net.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf"], version="official January 2025 report, data through December 2024", boundaries=["中文长研报与目录页码", "图表单位亿/万/百分比", "统计时点及地域口径", "描述性数据不可伪造因果关系"]),
]


def inspect_pdf(path: Path) -> dict:
    with pymupdf.open(path) as doc:
        if doc.is_encrypted or not 0 < len(doc) <= MAX_PAGES:
            raise ValueError("Encrypted, empty or over page limit")
        texts, pages = [], []
        for index, page in enumerate(doc):
            text = page.get_text(sort=True)
            texts.append(text)
            pages.append(dict(page=index + 1, text_chars=len(text), numeric_tokens=len(re.findall(r"\d+(?:[.,]\d+)*", text)), image_objects=len(page.get_images()), vector_paths=len(page.get_drawings()), figure_caption_clues=re.findall(r"(?im)^\s*(?:Figure\s+\d+[.:]?|Fig\.\s*\d+[.:]?|图\s*\d+[.：]?)\s*[^\n]{0,140}", text)[:12], table_caption_clues=re.findall(r"(?im)^\s*(?:Table\s+\d+[.:]?|表\s*\d+[.：]?)\s*[^\n]{0,140}", text)[:12]))
        full = "\n".join(texts)
        return dict(page_count=len(doc), length_band="short" if len(doc) <= 10 else "long" if len(doc) >= 40 else "medium", text_chars=len(full), numeric_tokens=sum(p["numeric_tokens"] for p in pages), image_objects=sum(p["image_objects"] for p in pages), vector_paths=sum(p["vector_paths"] for p in pages), low_text_pages=[p["page"] for p in pages if p["text_chars"] < 80], figure_caption_pages=[p["page"] for p in pages if p["figure_caption_clues"]], table_caption_pages=[p["page"] for p in pages if p["table_caption_clues"]], first_page_excerpt=texts[0][:1800], version_number_clues={term:len(re.findall(rf"\b{term}\b",full)) for term in ["5,179","5,172","5179","5172"]}, pages=pages)


def download(client: httpx.Client, urls: list[str], path: Path, failures: list) -> str:
    for url in urls:
        try:
            chunks, size = [], 0
            with client.stream("GET", url) as response:
                response.raise_for_status()
                for block in response.iter_bytes():
                    size += len(block)
                    if size > MAX_BYTES:
                        raise ValueError("PDF exceeds 50 MiB")
                    chunks.append(block)
                final_url = str(response.url)
            payload = b"".join(chunks)
            if not payload.startswith(b"%PDF-"):
                raise ValueError("Response is not a PDF")
            with pymupdf.open(stream=payload, filetype="pdf") as doc:
                if doc.is_encrypted or not 0 < len(doc) <= MAX_PAGES:
                    raise ValueError("Encrypted, empty or over page limit")
            path.write_bytes(payload)
            return url  # Preserve the reproducible endpoint, not expiring signed CDN redirects.
        except Exception as exc:
            failures.append(dict(url=url, error=str(exc), at=datetime.now(timezone.utc).isoformat()))
    raise RuntimeError(f"All download URLs failed for {path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Re-download and re-pin current publisher versions")
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    previous = {p["id"]:p for p in old.get("papers", [])}
    failures = old.get("download_failures", [])
    result = dict(schema_version=1, generated_at=datetime.now(timezone.utc).isoformat(), scope="10 independent publicly accessible papers/reports plus one derived scanned regression PDF", limits=dict(max_download_bytes=MAX_BYTES, max_pages=MAX_PAGES), observations_note="Object/caption counts are PDF extraction clues only. They do not prove chart, table, formula or scientific correctness. No LLM, OCR or scholarly verification is run by this preparation script.", papers=[], derived_variants=[], download_failures=failures)
    with httpx.Client(follow_redirects=True, timeout=90, headers={"User-Agent":"paperMind-public-research-corpus/1.0"}) as client:
        for source in PAPERS:
            paper = dict(source)
            path = DEST / f"{paper['id']}.pdf"
            try:
                paper["download_url"] = previous.get(paper["id"],{}).get("download_url",paper["download_urls"][0]) if path.exists() and not args.refresh else download(client,paper["download_urls"],path,failures)
                paper["downloaded_at"] = previous.get(paper["id"],{}).get("downloaded_at",datetime.now(timezone.utc).isoformat()) if not args.refresh else datetime.now(timezone.utc).isoformat()
                paper.update(file=str(path.relative_to(ROOT)).replace("\\","/"), bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), download_status="ok", **inspect_pdf(path))
                print(f"{paper['id']}: {paper['page_count']} pages, {paper['text_chars']} chars", flush=True)
            except Exception as exc:
                paper.update(download_status="failed", error=str(exc))
                print(f"{paper['id']}: FAILED {exc}", flush=True)
            result["papers"].append(paper)
    # A rasterized page of a downloaded source tests OCR activation. It is not a new study.
    source = next((p for p in result["papers"] if p["id"]=="attention" and p["download_status"]=="ok"), None)
    if source:
        scan_path=DEST / "attention-page3-scan.pdf"
        with pymupdf.open(ROOT/source["file"]) as doc, pymupdf.open() as scanned:
            page=doc[2]
            image=page.get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False)
            scanned.new_page(width=page.rect.width,height=page.rect.height).insert_image(page.rect,stream=image.tobytes("png"))
            scanned.save(scan_path,deflate=True)
        result["derived_variants"].append(dict(id="attention-page3-scan", title="Derived scanned page of Attention Is All You Need", derived_from="attention", source_page=3, purpose="OCR path regression, not an independent paper", file=str(scan_path.relative_to(ROOT)).replace("\\","/"),sha256=hashlib.sha256(scan_path.read_bytes()).hexdigest(),**inspect_pdf(scan_path)))
    MANIFEST.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return 0 if all(p["download_status"]=="ok" for p in result["papers"]) else 1


if __name__ == "__main__":
    sys.exit(main())
