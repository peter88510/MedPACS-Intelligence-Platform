"""DB layer package (session / engine).

Re-exports from `db.session` so existing callers keep using
`from db import get_db, SessionLocal, ...` unchanged after the 2026-06-09 relocate.
"""
from db.session import engine, SessionLocal, get_db, init_db, DATABASE_URL

__all__ = ["engine", "SessionLocal", "get_db", "init_db", "DATABASE_URL"]
