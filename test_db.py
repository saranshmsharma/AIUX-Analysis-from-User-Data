from database import engine, Base, get_db
from models import ShopifyCredentials
import sys

def test_connection():
    try:
        # Try to create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Test connection by getting a session
        db = next(get_db())
        db.execute("SELECT 1")
        print("✅ Database connection successful!")
        
        return True
    except Exception as e:
        print("❌ Database connection failed!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 