import ssl
import certifi
import requests
import sys
import os
from dotenv import load_dotenv

def test_ssl_certificates():
    print("\n=== SSL Certificate Test ===")
    
    # Test 1: Check Python SSL
    print("\n1. Testing Python SSL...")
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        print("✅ SSL Context created successfully")
        print(f"Certificate file location: {certifi.where()}")
    except Exception as e:
        print(f"❌ SSL Context Error: {str(e)}")

    # Test 2: Check certifi installation
    print("\n2. Testing certifi installation...")
    try:
        with open(certifi.where(), 'r') as cert_file:
            cert_data = cert_file.read()
            cert_count = cert_data.count('BEGIN CERTIFICATE')
            print(f"✅ Found {cert_count} certificates in certifi bundle")
    except Exception as e:
        print(f"❌ Certifi Error: {str(e)}")

    # Test 3: Test HTTPS connection to Shopify
    print("\n3. Testing HTTPS connection to Shopify...")
    try:
        load_dotenv()
        shop_url = os.getenv("SHOPIFY_SHOP_URL")
        if not shop_url:
            raise ValueError("SHOPIFY_SHOP_URL not found in .env file")
            
        url = f"https://{shop_url}"
        response = requests.get(url, verify=certifi.where())
        print(f"✅ Successfully connected to {url}")
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")

    # Test 4: Check Python version and SSL info
    print("\n4. Python and SSL Information:")
    print(f"Python Version: {sys.version}")
    print(f"OpenSSL Version: {ssl.OPENSSL_VERSION}")
    print(f"Default verify paths: {ssl.get_default_verify_paths()}")

    # Test 5: Verify Shopify API credentials
    print("\n5. Testing Shopify API credentials...")
    try:
        access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
        api_key = os.getenv("SHOPIFY_API_KEY")
        
        if not all([access_token, api_key]):
            raise ValueError("Missing Shopify credentials in .env file")
            
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        api_url = f"https://{shop_url}/admin/api/2024-01/shop.json"
        response = requests.get(api_url, headers=headers, verify=certifi.where())
        
        if response.status_code == 200:
            print("✅ Successfully authenticated with Shopify API")
            shop_data = response.json()['shop']
            print(f"Shop Name: {shop_data.get('name')}")
            print(f"Shop Email: {shop_data.get('email')}")
        else:
            print(f"❌ API Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Shopify API Error: {str(e)}")

if __name__ == "__main__":
    test_ssl_certificates() 