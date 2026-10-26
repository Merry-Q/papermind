"""Relocate a copied Windows paperMind SQLite snapshot to the Linux data mount."""

import hashlib
import json
import sqlite3
from pathlib import Path, PureWindowsPath


DATA = Path("/var/lib/papermind")
HOST_DATA = Path("/opt/papermind/data")
DB = HOST_DATA / "papermind.db"


def relocate(value):
    if isinstance(value, str) and len(value) > 3 and value[1:3] == ":\\":
        parts = PureWindowsPath(value).parts
        lower = [part.lower() for part in parts]
        if "papermind" in lower and "data" in lower:
            index = lower.index("data", lower.index("papermind") + 1)
            return str(DATA.joinpath(*parts[index + 1 :]))
    if isinstance(value, list):
        return [relocate(item) for item in value]
    if isinstance(value, dict):
        return {key: relocate(item) for key, item in value.items()}
    return value


def encode(value):
    return json.dumps(value, ensure_ascii=False)


def main():
    conn = sqlite3.connect(str(DB))
    assert conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    rewritten = 0
    with conn:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            columns = [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')]
            if "payload" not in columns:
                continue
            for rowid, raw in conn.execute(f'SELECT rowid, payload FROM "{table}"'):
                try:
                    value = json.loads(raw)
                except (TypeError, ValueError):
                    continue
                updated = relocate(value)
                if updated != value:
                    conn.execute(f'UPDATE "{table}" SET payload=? WHERE rowid=?', (encode(updated), rowid))
                    rewritten += 1

        # Reading edition hashes include the PDF path. Relocation changes the path,
        # while the document content remains identical.
        docs = {json.loads(raw)["id"]: json.loads(raw) for (raw,) in conn.execute("SELECT payload FROM documents")}
        for rowid, raw in conn.execute("SELECT rowid, payload FROM reading_editions"):
            edition = json.loads(raw)
            doc = docs.get(edition["document_id"])
            if not doc or not edition.get("base_hash"):
                continue
            source = {"nodes": doc["nodes"], "sources": doc["sources"], "file": doc.get("file_path")}
            edition["base_hash"] = hashlib.sha256(encode(source).encode()).hexdigest()
            conn.execute("UPDATE reading_editions SET payload=? WHERE rowid=?", (encode(edition), rowid))

    assert conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    for (raw,) in conn.execute("SELECT payload FROM documents"):
        doc = json.loads(raw)
        for field in ("file_path", "ir_path"):
            path = doc.get(field)
            if path:
                assert path.startswith(str(DATA) + "/"), (doc["id"], field)
                assert HOST_DATA.joinpath(Path(path).relative_to(DATA)).is_file(), (doc["id"], field, path)
    print(f"Migrated {rewritten} JSON rows; {len(docs)} documents and their files verified")


if __name__ == "__main__":
    main()
