"""
Database connection and session management
"""

import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text, func, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base

logger = logging.getLogger(__name__)

# Get database URL from environment or use SQLite as default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quantcoach_interviews.db")

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL query logging
    )
    logger.info(f"📦 Using SQLite database: {DATABASE_URL}")
else:
    # PostgreSQL or other database
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20,
        echo=False
    )
    logger.info(f"📦 Using database: {DATABASE_URL.split('@')[0]}@...")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database
    Creates all tables defined in models.py
    """
    try:
        logger.info("🔨 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")

        # Log created tables
        table_names = Base.metadata.tables.keys()
        logger.info(f"📊 Created {len(table_names)} tables: {', '.join(table_names)}")

    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


def get_db() -> Session:
    """
    Dependency for getting database sessions
    Use with FastAPI Depends()

    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions
    Use for non-FastAPI code

    Example:
        with get_db_context() as db:
            candidates = db.query(Candidate).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_db():
    """
    Reset database (drop all tables and recreate)
    WARNING: This will delete all data!
    Only use in development!
    """
    logger.warning("⚠️ RESETTING DATABASE - ALL DATA WILL BE LOST!")
    Base.metadata.drop_all(bind=engine)
    logger.info("🗑️ All tables dropped")
    init_db()
    logger.info("✅ Database reset complete")


def get_table_counts():
    """
    Get row counts for all tables
    Useful for debugging and monitoring

    Returns:
        dict: Table name -> row count
    """
    counts = {}
    with get_db_context() as db:
        for table_name, table in Base.metadata.tables.items():
            try:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                counts[table_name] = count
            except Exception as e:
                logger.error(f"Error counting {table_name}: {e}")
                counts[table_name] = -1

    return counts


def check_db_health():
    """
    Check database connection health

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        logger.info("✅ Database health check passed")
        return True
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False
