import shopify
import os
import requests
import certifi
import logging
from dotenv import load_dotenv
from typing import Dict, Optional, List
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('ShopifyClient')

# Create a file handler
fh = logging.FileHandler('shopify_debug.log')
fh.setLevel(logging.DEBUG)

# Create a console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

load_dotenv()

class ShopifyClient:
    def __init__(self, shop_url: Optional[str] = None, access_token: Optional[str] = None):
        """Initialize Shopify client with credentials from env or parameters"""
        logger.info("Initializing ShopifyClient")
        
        self.shop_url = shop_url or os.getenv("SHOPIFY_SHOP_URL")
        self.access_token = access_token or os.getenv("SHOPIFY_ACCESS_TOKEN")
        
        if not self.shop_url or not self.access_token:
            logger.error("Missing credentials")
            raise ValueError("Shopify credentials not provided")
        
        # Clean up shop URL
        self.shop_url = self.shop_url.strip('/')  # Remove trailing slashes
        self.shop_url = self.shop_url.replace('https://', '').replace('http://', '')
        self.shop_url = self.shop_url.replace('.myshopify.com', '')  # Remove if exists
        self.shop_url = f"{self.shop_url}.myshopify.com"  # Add back correctly
        
        logger.debug(f"Shop URL: {self.shop_url}")
        logger.debug(f"Access Token: {'*' * (len(self.access_token) if self.access_token else 0)}")
        logger.info(f"Initialized with shop URL: {self.shop_url}")

    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None) -> Optional[Dict]:
        """Make a request to Shopify API with detailed logging"""
        api_url = f"https://{self.shop_url}/admin/api/2024-01/{endpoint}"
        headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"Making {method} request to: {api_url}")
        logger.debug(f"Request params: {params}")
        logger.debug(f"Request headers: {headers}")
        
        try:
            response = requests.request(
                method=method,
                url=api_url,
                headers=headers,
                params=params,
                verify=certifi.where()
            )
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    logger.error(f"Failed to decode JSON response. Response text: {response.text[:500]}")
                    return None
            else:
                logger.error(f"API Error: Status code {response.status_code}")
                logger.error(f"Response body: {response.text[:500]}")
                return None
                
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error: {str(e)}")
            logger.error(f"SSL Certificate path: {certifi.where()}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return None

    def get_shop_info(self) -> Optional[Dict]:
        """Get basic shop information using requests"""
        logger.info("Getting shop information")
        
        try:
            response = self._make_request('shop.json')
            
            if response and 'shop' in response:
                shop_data = response['shop']
                logger.info("Successfully retrieved shop information")
                return {
                    'name': shop_data.get('name'),
                    'email': shop_data.get('email'),
                    'domain': shop_data.get('domain'),
                    'country': shop_data.get('country_name'),
                    'currency': shop_data.get('currency'),
                    'timezone': shop_data.get('timezone')
                }
            else:
                logger.error("Failed to get shop information")
                return None
                
        except Exception as e:
            logger.error(f"Error getting shop info: {str(e)}", exc_info=True)
            return None

    def get_products(self, limit: int = 50) -> List[Dict]:
        """Get products from the shop"""
        logger.info(f"Getting products (limit: {limit})")
        
        try:
            response = self._make_request('products.json', params={'limit': limit})
            
            if response and 'products' in response:
                products = response['products']
                logger.info(f"Successfully retrieved {len(products)} products")
                return [{
                    'id': product['id'],
                    'title': product['title'],
                    'vendor': product['vendor'],
                    'product_type': product['product_type'],
                    'created_at': product['created_at'],
                    'updated_at': product['updated_at'],
                    'variants': [{
                        'id': variant['id'],
                        'price': variant['price'],
                        'sku': variant.get('sku'),
                        'inventory_quantity': variant.get('inventory_quantity', 0)
                    } for variant in product['variants']]
                } for product in products]
            
            logger.error("Failed to get products")
            return []
            
        except Exception as e:
            logger.error(f"Error getting products: {str(e)}", exc_info=True)
            return []

    def get_orders(self, limit: int = 50) -> List[Dict]:
        """Get orders from the shop"""
        try:
            headers = {
                'X-Shopify-Access-Token': self.access_token,
                'Content-Type': 'application/json'
            }
            
            api_url = f"https://{self.shop_url}/admin/api/2024-01/orders.json?limit={limit}&status=any"
            response = requests.get(api_url, headers=headers, verify=certifi.where())
            
            if response.status_code == 200:
                orders = response.json()['orders']
                return [{
                    'id': order['id'],
                    'created_at': order['created_at'],
                    'total_price': order['total_price'],
                    'currency': order['currency'],
                    'customer': {
                        'email': order.get('email'),
                        'first_name': order.get('customer', {}).get('first_name'),
                        'last_name': order.get('customer', {}).get('last_name')
                    } if order.get('customer') else None
                } for order in orders]
            return []
            
        except Exception as e:
            print(f"Error getting orders: {str(e)}")
            return []

    def get_analytics_data(self) -> Optional[Dict]:
        """Get basic analytics data"""
        try:
            orders = self.get_orders()
            products = self.get_products()
            
            total_sales = sum(float(order['total_price']) for order in orders)
            total_orders = len(orders)
            avg_order_value = total_sales / total_orders if total_orders > 0 else 0
            total_products = len(products)
            
            return {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'average_order_value': avg_order_value,
                'total_products': total_products
            }
        except Exception as e:
            print(f"Error getting analytics data: {str(e)}")
            return None

    def close_session(self):
        """Close the Shopify session"""
        try:
            shopify.ShopifyResource.clear_session()
        except Exception as e:
            print(f"Error closing session: {str(e)}")

    def get_customers(self):
        customers = []

        try:
            customers_data = shopify.Customer.find(limit=250)

            for customer in customers_data:
                customers.append({
                    'id': customer.id,
                    'email': customer.email,
                    'orders_count': customer.orders_count,
                    'total_spent': float(customer.total_spent),
                    'created_at': customer.created_at
                })

        except Exception as e:
            raise Exception(f"Failed to fetch customers: {str(e)}")

        return customers