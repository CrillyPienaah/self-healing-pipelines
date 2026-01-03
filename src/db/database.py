"""
Database Configuration
PostgreSQL connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/self_healing_pipelines'
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries (disable in production)
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency for FastAPI endpoints.
    Yields database session and ensures cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Run this once during deployment.
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)
    print('✓ Database tables created successfully')


def drop_db():
    """
    Drop all tables (use with caution!)
    """
    from .models import Base
    Base.metadata.drop_all(bind=engine)
    print('✓ Database tables dropped')