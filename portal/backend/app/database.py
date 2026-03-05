"""Database setup with SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings

engine = create_engine(settings.db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and run lightweight migrations."""
    Base.metadata.create_all(bind=engine)
    # Add columns that may not exist in older databases
    _migrate_add_columns()


def _migrate_add_columns():
    """Add new columns to existing tables if missing."""
    import sqlite3
    db_path = settings.db_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def existing_cols(table):
        cursor.execute(f"PRAGMA table_info({table})")
        return {row[1] for row in cursor.fetchall()}

    # gstins table
    cols = existing_cols("gstins")
    for col, defn in [
        ("portal_username", "VARCHAR(100)"),
        ("portal_password", "VARCHAR(100)"),
        ("company_id",      "INTEGER"),
    ]:
        if col not in cols:
            cursor.execute(f"ALTER TABLE gstins ADD COLUMN {col} {defn}")

    # upload_logs table
    cols = existing_cols("upload_logs")
    if "company_id" not in cols:
        cursor.execute("ALTER TABLE upload_logs ADD COLUMN company_id INTEGER")

    # filing_sessions table
    cols = existing_cols("filing_sessions")
    if "company_id" not in cols:
        cursor.execute("ALTER TABLE filing_sessions ADD COLUMN company_id INTEGER")

    # companies table — add slug if missing
    cols = existing_cols("companies")
    if "slug" not in cols:
        cursor.execute("ALTER TABLE companies ADD COLUMN slug VARCHAR(100)")
        # Back-fill slugs for existing companies
        cursor.execute("SELECT id, name FROM companies")
        for cid, cname in cursor.fetchall():
            slug = _make_slug(cname)
            cursor.execute("UPDATE companies SET slug=? WHERE id=?", (slug, cid))

    conn.commit()
    conn.close()


def _make_slug(name: str) -> str:
    """Convert company name to a folder-safe slug."""
    import re
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "company"
