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

def init_db():
    Base.metadata.create_all(bind=engine)
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
