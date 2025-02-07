import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def test_db_connection():
    try:
        # Get credentials from .env
        db_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "sslmode": "require"
        }
        
        # Print connection params (remove in production)
        print("Attempting to connect with:")
        for key, value in db_params.items():
            if key != "password":
                print(f"{key}: {value}")
        
        # Try to connect
        conn = psycopg2.connect(**db_params)
        print("Successfully connected to the database!")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_db_connection() 