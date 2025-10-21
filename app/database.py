from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database engine with improved pool settings for production
engine = create_engine(
    settings.database_url,
    echo=False,  # Disable SQL echo to reduce logs
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_size=10,  # Base pool size
    max_overflow=20,  # Additional connections when needed
    pool_timeout=60,  # Wait up to 60 seconds for connection
    connect_args={
        "connect_timeout": 60,
        "read_timeout": 60,
        "write_timeout": 60
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
