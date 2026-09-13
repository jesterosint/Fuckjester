"""SQLite + парсер .txt/.csv/.json/.rar."""
from __future__ import annotations

import csv
import json
import logging
import re
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Optional

try:
    import rarfile
    RAR_OK = True
except ImportError:
    RAR_OK = False

LOG = logging.getLogger("fuckjester.storage")

BASE = Path(__file__).resolve().parent.parent
DB_DIR = BASE / "data" / "databases"
ARCH_DIR = BASE / "data" / "archives"
GEN_DIR = BASE / "data" / "generated"
for d in (DB_DIR, ARCH_DIR, GEN_DIR):
    d.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "fuckjester.db"
GEN_DB_PATH = DB_DIR / "generated.db"

MAX_FILE_SIZE = 500 * 1024 * 1024
DELIMITERS = [":", ";", "|", ",", "\t"]


@contextmanager
def _conn(path: Path = DB_PATH) -> Iterator:
    conn = __import__("sqlite3").connect(str(path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init() -> None:
    """Создаёт таблицы."""
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_records_source ON records(source);
            CREATE INDEX IF NOT EXISTS idx_records_content ON records(content);
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                records_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
        """)
    with _conn(GEN_DB_PATH) as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)


# ---------- парсер файлов ----------

def _detect_encoding(raw: bytes) -> str:
    for enc in ("utf-8", "cp1251", "latin-1"):
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def _safe_extract_rar(rar_path: Path, dest: Path) -> list[Path]:
    if not RAR_OK:
        raise RuntimeError("rarfile не установлен: pip install rarfile")
    dest.mkdir(parents=True, exist_ok=True)
    dest_res = dest.resolve()
    out: list[Path] = []
    with rarfile.RarFile(str(rar_path)) as rf:
        for info in rf.infolist():
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or ".." in name.split("/"):
                LOG.warning("Пропущен небезопасный путь: %s", name)
                continue
            target = (dest / name).resolve()
            if not str(target).startswith(str(dest_res)):
                LOG.warning("Path traversal: %s", name)
                continue
            rf.extract(info, str(dest))
            out.append(dest / name)
    return out


def _iter_txt(path: Path) -> Iterator[str]:
    enc = _detect_encoding(path.open("rb").read(8192))
    with path.open("r", encoding=enc, errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


def _iter_csv(path: Path) -> Iterator[str]:
    enc = _detect_encoding(path.open("rb").read(8192))
    with path.open("r", encoding=enc, errors="replace", newline="") as f:
        try:
            dialect = csv.Sniffer().sniff(f.read(4096), delimiters=",;|\t:")
            f.seek(0)
            for row in csv.reader(f, dialect):
                line = " | ".join(c.strip() for c in row if c.strip())
                if line:
                    yield line
        except Exception:
            f.seek(0)
            for line in f:
                line = line.strip()
                if line:
                    yield line


def _iter_json(path: Path) -> Iterator[str]:
    enc = _detect_encoding(path.open("rb").read(8192))
    with path.open("r", encoding=enc, errors="replace") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield json.dumps(item, ensure_ascii=False)
            elif isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, list):
                        for item in v:
                            yield json.dumps({k: item}, ensure_ascii=False)
                    else:
                        yield json.dumps({k: v}, ensure_ascii=False)
        except json.JSONDecodeError:
            f.seek(0)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    yield line
                except json.JSONDecodeError:
                    continue


def _normalize(line: str) -> str:
    for d in DELIMITERS:
        if d in line:
            parts = [p.strip() for p in line.split(d) if p.strip()]
            return " | ".join(parts) if parts else line.strip()
    return line.strip()


def iter_file(path: Path) -> Iterator[str]:
    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f"Файл слишком большой (>500 МБ): {path}")
    suffix = path.suffix.lower()
    src = {".txt": _iter_txt, ".csv": _iter_csv, ".json": _iter_json}.get(suffix, _iter_txt)
    for line in src(path):
        norm = _normalize(line)
        if norm:
            yield norm


def collect_files(path: Path) -> list[Path]:
    supported = {".txt", ".csv", ".json"}
    out: list[Path] = []

    def _handle(p: Path) -> None:
        if p.suffix.lower() in supported and p.is_file():
            out.append(p)
        elif p.suffix.lower() == ".rar" and p.is_file():
            try:
                for f in _safe_extract_rar(p, ARCH_DIR / p.stem):
                    if f.suffix.lower() in supported and f.is_file():
                        out.append(f)
            except Exception as e:
                LOG.warning("RAR не распакован %s: %s", p, e)

    if path.is_file():
        _handle(path)
    elif path.is_dir():
        for p in path.rglob("*"):
            _handle(p)
    return out


# ---------- БД ----------

def add_records(source: str, records: Iterable[str]) -> int:
    now = datetime.utcnow().isoformat()
    count = 0
    with _conn() as c:
        cur = c.cursor()
        batch: list[tuple] = []
        for content in records:
            if not content:
                continue
            batch.append((source, content, now))
            if len(batch) >= 1000:
                cur.executemany(
                    "INSERT INTO records (source, content, created_at) VALUES (?,?,?)",
                    batch,
                )
                count += len(batch)
                batch.clear()
        if batch:
            cur.executemany(
                "INSERT INTO records (source, content, created_at) VALUES (?,?,?)",
                batch,
            )
            count += len(batch)
        cur.execute(
            """INSERT INTO sources (name, records_count, created_at) VALUES (?,?,?)
               ON CONFLICT(name) DO UPDATE SET records_count = records_count + excluded.records_count""",
            (source, count, now),
        )
    return count


def list_sources() -> list[tuple]:
    with _conn() as c:
        return c.execute(
            "SELECT id, name, records_count, created_at FROM sources ORDER BY id DESC"
        ).fetchall()


def delete_source(sid: int) -> int:
    with _conn() as c:
        cur = c.cursor()
        cur.execute("SELECT name FROM sources WHERE id=?", (sid,))
        row = cur.fetchone()
        if not row:
            return 0
        cur.execute("DELETE FROM records WHERE source=?", (row[0],))
        n = cur.rowcount
        cur.execute("DELETE FROM sources WHERE id=?", (sid,))
        return n


def merge_sources(new_name: str, ids: list[int]) -> int:
    with _conn() as c:
        cur = c.cursor()
        ph = ",".join("?" * len(ids))
        cur.execute(f"SELECT name FROM sources WHERE id IN ({ph})", ids)
        names = [r[0] for r in cur.fetchall()]
        if not names:
            return 0
        nph = ",".join("?" * len(names))
        cur.execute(f"UPDATE records SET source=? WHERE source IN ({nph})",
                    [new_name, *names])
        n = cur.rowcount
        cur.execute(f"DELETE FROM sources WHERE id IN ({ph})", ids)
        cur.execute(
            "INSERT OR REPLACE INTO sources (name, records_count, created_at) VALUES (?,?,?)",
            (new_name, n, datetime.utcnow().isoformat()),
        )
        return n


def deduplicate(source: Optional[str] = None) -> int:
    with _conn() as c:
        cur = c.cursor()
        if source:
            cur.execute(
                """DELETE FROM records WHERE source=? AND id NOT IN (
                   SELECT MIN(id) FROM records WHERE source=? GROUP BY content)""",
                (source, source),
            )
        else:
            cur.execute(
                """DELETE FROM records WHERE id NOT IN (
                   SELECT MIN(id) FROM records GROUP BY content)"""
            )
        return cur.rowcount


def total_records() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM records").fetchone()[0]


def search(query: str, limit: int = 200) -> list[tuple]:
    like = f"%{query}%"
    with _conn() as c:
        return c.execute(
            "SELECT id, source, content, created_at FROM records WHERE content LIKE ? LIMIT ?",
            (like, limit),
        ).fetchall()


def export_records(path: Path, source: Optional[str] = None) -> int:
    with _conn() as c:
        if source:
            rows = c.execute(
                "SELECT id, source, content, created_at FROM records WHERE source=?",
                (source,),
            ).fetchall()
        else:
            rows = c.execute("SELECT id, source, content, created_at FROM records").fetchall()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "source", "content", "created_at"])
        w.writerows(rows)
    return len(rows)


def save_person(data: str) -> None:
    with _conn(GEN_DB_PATH) as c:
        c.execute("INSERT INTO persons (data, created_at) VALUES (?,?)",
                  (data, datetime.utcnow().isoformat()))


def fetch_persons(limit: int = 100) -> list[tuple]:
    with _conn(GEN_DB_PATH) as c:
        return c.execute(
            "SELECT id, data, created_at FROM persons ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def search_phone(q: str, limit: int = 200) -> list[tuple]:
    digits = re.sub(r"\D", "", q)
    return search(digits, limit) if len(digits) >= 5 else []