"""Export published editions for GitHub Pages; never starts jobs or calls models."""
import argparse
import json
from pathlib import Path, PureWindowsPath
import re
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.reading_v2 import frame_html


def build(output: Path):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'readings').mkdir(exist_ok=True)
    (output / 'pdfs').mkdir(exist_ok=True)
    with sqlite3.connect((ROOT / 'data/papermind.db').as_uri() + '?mode=ro', uri=True) as db:
        documents = {key: json.loads(raw) for key, raw in db.execute('SELECT id,payload FROM documents')}
        editions = {key: json.loads(raw) for key, raw in db.execute('SELECT id,payload FROM reading_editions')}
        defaults = db.execute('SELECT document_id,edition_id FROM reading_defaults ORDER BY rowid DESC').fetchall()
    catalog = []
    for did, eid in defaults:
        if not re.fullmatch(r'pdf-[a-f0-9]+', did) or not re.fullmatch(r'[a-f0-9-]{36}', eid):
            raise ValueError('Invalid document/edition identifier')
        doc, edition = documents[did], editions[eid]
        if doc.get('is_demo') or edition['status'] not in {'completed', 'validated'}:
            continue
        folder = ROOT / 'data/reading-v2' / eid
        artifact = json.loads((folder / 'artifact.json').read_text(encoding='utf-8'))
        evidence = json.loads((folder / 'data.json').read_text(encoding='utf-8'))
        page = frame_html(artifact, evidence, edition, 'github-pages', standalone=True)
        (output / 'readings' / f'{did}.html').write_text(page, encoding='utf-8')
        # Stored paths originate on Windows. Resolve only the basename inside uploads.
        name = PureWindowsPath(doc['file_path']).name
        pdf = ROOT / 'data/uploads' / name
        if not pdf.is_file() or pdf.suffix.lower() != '.pdf':
            raise FileNotFoundError(f'Original PDF missing for {did}')
        shutil.copyfile(pdf, output / 'pdfs' / f'{did}.pdf')
        catalog.append({'id': did, 'title': doc['title'], 'readingTitle': artifact['title'],
                        'description': artifact['description'], 'pages': doc.get('page_count', 0),
                        'reading': f'readings/{did}.html', 'pdf': f'pdfs/{did}.pdf'})
    if not catalog:
        raise ValueError('No published readings available')
    (output / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False), encoding='utf-8')
    for name in ('index.html', 'styles.css', 'app.js'):
        shutil.copyfile(ROOT / 'frontend/pages' / name, output / name)
    (output / '.nojekyll').touch()
    print(f'Exported {len(catalog)} published readings and original PDFs to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.pages/site')
    build(parser.parse_args().output)
