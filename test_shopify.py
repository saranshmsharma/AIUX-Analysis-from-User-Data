import os
from dotenv import load_dotenv
import shopify

# Load environment variables
load_dotenv()

def test_shopify_connection():
    print("Testing Shopify Connection...")
    
    # Get credentials from environment
    shop_url = os.getenv("SHOPIFY_SHOP_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    
    print(f"Shop URL: {shop_url}")
    print(f"Access Token: {'*' * len(access_token) if access_token else 'Not found'}")
    
    try:
        # Initialize Shopify session
        api_version = '2024-01'
        shop_url = f"https://{shop_url}" if not shop_url.startswith('http') else shop_url
        print(f"Connecting to: {shop_url}")
        
        session = shopify.Session(shop_url, api_version, access_token)
        shopify.ShopifyResource.activate_session(session)
        
        # Try to get shop info
        shop = shopify.Shop.current()
        print("\nConnection Successful!")
        print(f"Shop Name: {shop.name}")
        print(f"Shop Email: {shop.email}")
        print(f"Shop Domain: {shop.domain}")
        
        return True
        
    except Exception as e:
        print(f"\nError connecting to Shopify: {str(e)}")
        print("\nPlease verify:")
        print("1. Your shop URL is in the format: your-store.myshopify.com")
        print("2. Your access token is correct")
        print("3. The app has the necessary permissions")
        return False
    finally:
        try:
            shopify.ShopifyResource.clear_session()
        except:
            pass

if __name__ == "__main__":
    test_shopify_connection() 