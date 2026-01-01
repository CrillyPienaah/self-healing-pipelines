from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.monitoring.models import Base
import os

# For now, use SQLite (will switch to PostgreSQL later)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./pipeline_monitor.db')

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    '''Initialize database tables'''
    Base.metadata.create_all(bind=engine)


def get_db():
    '''Dependency for FastAPI to get database session'''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
