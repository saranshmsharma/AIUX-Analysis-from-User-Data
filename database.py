from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import logging
from pathlib import Path
from typing import Generator  # Import Generator
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create data directory if it doesn't exist
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Create SQLite database URL
DATABASE_URL = f"sqlite:///{data_dir}/shop_ai.db"

# Create engine for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session as a context manager"""
    db = SessionLocal()
    try:
        yield db  # Yield the session
    finally:
        db.close()  # Ensure the session is closed

def init_db():
    """Initialize database"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
            
    except SQLAlchemyError as e:
        logger.error(f"Database error during initialization: {str(e)}")
        raise

def check_db_connection():
    """Check database connection status"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

def setup_database():
    """Complete database setup process"""
    try:
        # Initialize database schema
        init_db()
        
        # Verify connection
        if not check_db_connection():
            raise Exception("Failed to verify database connection")
        
        logger.info("Database setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False