"""Single-document interactive reading build; publish immediately on success."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend import reading_v2 as reading

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--document',required=True);p.add_argument('--resume');p.add_argument('--interface');a=p.parse_args()
    interface=json.loads(Path(a.interface).read_text(encoding='utf-8')) if a.interface else None
    item=reading.get(a.resume) if a.resume else reading.create(a.document)
    if item['document_id']!=a.document:raise ValueError('重试文档不匹配')
    print(json.dumps({'edition':item['id'],'document':a.document},ensure_ascii=False),flush=True)
    result=reading.generate(item['id'],interface)
    print(json.dumps(result,ensure_ascii=False),flush=True)
