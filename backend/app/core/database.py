from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True if "postgresql" in settings.SYNC_DATABASE_URL else False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SYNC_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _ensure_columns(db, additions: list):
    """Add missing columns for both PostgreSQL and SQLite.

    Each entry: (table, column, col_type, default_value_or_None)
    """
    from sqlalchemy import text
    dialect = engine.dialect.name

    for table, col, col_type, default in additions:
        if dialect == "postgresql":
            db.execute(text(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}"
                + (f" DEFAULT {default}" if default else "")
            ))
        elif dialect == "sqlite":
            existing = [r[1] for r in db.execute(text(f"PRAGMA table_info({table})"))]
            if col not in existing:
                ddl = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                if default:
                    ddl += f" DEFAULT {default}"
                db.execute(text(ddl))


def init_db():
    Base.metadata.create_all(bind=engine)

    # Safety net: add new columns for existing tables
    db = SessionLocal()
    try:
        _ensure_columns(db, [
            ("interview_reports", "status", "VARCHAR(20)", "'pending'"),
            ("recordings", "summary_json", "TEXT", None),
            ("recordings", "qa_json", "TEXT", None),
        ])
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    # Ensure default user exists (needed for FK constraints with PostgreSQL)
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.core.security import hash_password
        if not db.query(User).filter(User.id == "default").first():
            db.add(User(id="default", username="default", password_hash=hash_password("default")))
            db.commit()
    finally:
        db.close()
