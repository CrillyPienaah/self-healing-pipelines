"""
Database Configuration
PostgreSQL connection with graceful error handling for cloud deployment
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

# Create engine with error handling
try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Disable verbose SQL logging in production
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10,
        connect_args={'connect_timeout': 10}
    )
    print('✓ Database engine created successfully')
except Exception as e:
    print(f'⚠ Database engine creation failed: {e}')
    print('⚠ App will start without database (read-only mode)')
    engine = None

# Session factory
if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None


def get_db():
    """
    Dependency for FastAPI endpoints.
    Yields database session and ensures cleanup.
    """
    if not SessionLocal:
        raise Exception('Database not available')
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Only runs if engine is available.
    """
    if not engine:
        print('⚠ Cannot initialize database - engine not available')
        return False
    
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
        print('✓ Database tables created successfully')
        return True
    except Exception as e:
        print(f'⚠ Database initialization failed: {e}')
        return False


def drop_db():
    """
    Drop all tables (use with caution!)
    """
    if not engine:
        print('⚠ Cannot drop database - engine not available')
        return False
    
    try:
        from .models import Base
        Base.metadata.drop_all(bind=engine)
        print('✓ Database tables dropped')
        return True
    except Exception as e:
        print(f'⚠ Database drop failed: {e}')
        return False