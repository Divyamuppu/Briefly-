"""
Neon (PostgreSQL) data-access layer for Briefly.

Drop-in replacement for the previous Supabase helpers: every function keeps the
same name, signature, and return shape, so the rest of server.py is unchanged.
Talks to Neon over a real Postgres connection (psycopg2) using a single
DATABASE_URL (Neon's pooled connection string, sslmode=require).
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import contextmanager

from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

# Safety net so DATABASE_URL is available even if this module is imported
# before server.py runs its own load_dotenv().
load_dotenv(Path(__file__).parent / ".env")

logger = logging.getLogger(__name__)

# Lazily created so DATABASE_URL is read at first use (after env is loaded),
# not at import time.
_pool: Optional[ThreadedConnectionPool] = None


def _get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        dsn = os.environ["DATABASE_URL"]
        # Small pool: the API calls these helpers via asyncio.to_thread (sync).
        _pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=dsn)
        logger.info("Initialized Neon connection pool")
    return _pool


@contextmanager
def _cursor():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            conn.commit()
        finally:
            cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def _slug(title: str) -> str:
    """Stable, readable id derived from a card title (matches the frontend)."""
    slug = title.strip().lower().replace(" ", "_")
    for ch in ["$", "#", "[", "]", "/", "."]:
        slug = slug.replace(ch, "")
    return slug


def _card_row_to_dict(row) -> dict:
    merged = dict(row.get("data") or {})
    merged["_slug"] = row["slug"]
    return merged


def cards_get_all() -> Dict[str, List[dict]]:
    with _cursor() as cur:
        cur.execute("SELECT category, slug, data FROM cards")
        rows = cur.fetchall()
    result: Dict[str, List[dict]] = {}
    for row in rows:
        result.setdefault(row["category"], []).append(_card_row_to_dict(row))
    return result


def cards_resync_category(category: str, items: List[dict]):
    with _cursor() as cur:
        cur.execute("DELETE FROM cards WHERE category = %s", (category,))
        for item in items:
            cur.execute(
                "INSERT INTO cards (category, slug, data) VALUES (%s, %s, %s)",
                (category, _slug(item["title"]), psycopg2.extras.Json(item)),
            )


def video_types_get_all() -> Dict[str, dict]:
    with _cursor() as cur:
        cur.execute("SELECT id, data FROM video_types")
        rows = cur.fetchall()
    return {row["id"]: row["data"] for row in rows}


def video_types_resync(seed_data: Dict[str, dict]):
    with _cursor() as cur:
        cur.execute("DELETE FROM video_types")
        for type_id, data in seed_data.items():
            cur.execute(
                "INSERT INTO video_types (id, data) VALUES (%s, %s)",
                (type_id, psycopg2.extras.Json(data)),
            )


def project_get(project_id: str) -> Optional[dict]:
    with _cursor() as cur:
        cur.execute("SELECT id, data FROM projects WHERE id = %s", (project_id,))
        row = cur.fetchone()
    if not row:
        return None
    merged = dict(row.get("data") or {})
    merged["id"] = str(row["id"])
    return merged


def project_create(project_id: str, data: dict):
    with _cursor() as cur:
        cur.execute(
            "INSERT INTO projects (id, data) VALUES (%s, %s)",
            (project_id, psycopg2.extras.Json(data)),
        )


def project_update(project_id: str, updates: dict):
    existing = project_get(project_id)
    if existing is None:
        raise ValueError(f"Project {project_id} not found")
    merged = {**existing, **updates}
    merged.pop("id", None)
    with _cursor() as cur:
        cur.execute(
            "UPDATE projects SET data = %s WHERE id = %s",
            (psycopg2.extras.Json(merged), project_id),
        )


def swipe_create(swipe_id: str, project_id: str, card_id: str, action: str):
    with _cursor() as cur:
        cur.execute(
            "INSERT INTO swipes (id, project_id, card_id, action) VALUES (%s, %s, %s, %s)",
            (swipe_id, project_id, card_id, action),
        )


def swipes_get_for_project(project_id: str) -> List[dict]:
    with _cursor() as cur:
        cur.execute(
            "SELECT id, project_id, card_id, action FROM swipes WHERE project_id = %s",
            (project_id,),
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]
