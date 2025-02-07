import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

# Shopify configuration
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL', 'your-store.myshopify.com')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR}/data/shopai.db")

# Shared database configuration
SHARED_DATA_DIR = BASE_DIR / "data"
SHARED_DATA_DIR.mkdir(exist_ok=True)
SHARED_DB_PATH = SHARED_DATA_DIR / "shopai_predictai.db"

# Shared database URL
DATABASE_URL = f"sqlite:///{SHARED_DB_PATH}"

# Shared environment variables with defaults
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Check only critical environment variables
critical_vars = ['OPENAI_API_KEY']  # Only check OpenAI key as critical
missing_vars = [var for var in critical_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing critical environment variables: {', '.join(missing_vars)}") 