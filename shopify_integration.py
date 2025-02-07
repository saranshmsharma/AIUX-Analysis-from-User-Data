import os
import shopify
import pandas as pd
from datetime import datetime, timedelta
import logging
import ssl
import certifi
from openai import OpenAI
import json

# Ensure Python knows where to find the root certificates
os.environ["SSL_CERT_FILE"] = certifi.where()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShopifyIntegration:
    def __init__(self, access_token, shop_url=None):
        self.access_token = access_token
        self.shop_url = shop_url or "your-store.myshopify.com"
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.setup_session()

    def setup_session(self):
        """Initialize Shopify session."""
        try:
            # Format shop URL correctly
            if not self.shop_url.startswith('https://'):
                self.shop_url = f"https://{self.shop_url}"
            if not self.shop_url.endswith('.myshopify.com'):
                self.shop_url = f"{self.shop_url}.myshopify.com"

            # Initialize Shopify session with the given access token and shop URL
            shopify.Session.setup(api_key=self.access_token, secret=None)
            self.session = shopify.Session(self.shop_url, '2024-01', self.access_token)
            shopify.ShopifyResource.activate_session(self.session)
            
            # Configure SSL verification explicitly
            shopify.ShopifyResource.ssl_verify = True
            shopify.ShopifyResource.ca_file = certifi.where()
            
            logger.info("Shopify session initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Shopify session: {str(e)}")
            raise

    def validate_connection(self):
        """Validate the Shopify connection."""
        try:
            shop = shopify.Shop.current()
            return {
                'name': shop.name,
                'email': shop.email,
                'domain': shop.domain
            }
        except Exception as e:
            logger.error(f"Shopify validation error: {str(e)}")
            raise Exception(f"Connection error: {str(e)}")

    def get_store_data(self):
        """Get all relevant store data with AI-powered insights."""
        try:
            # Fetch data from Shopify
            orders = shopify.Order.find(status='any', limit=250)
            products = shopify.Product.find(limit=250)
            customers = shopify.Customer.find(limit=250)

            # Process orders
            total_sales = sum(float(order.total_price) for order in orders)
            total_orders = len(orders)
            avg_order_value = total_sales / total_orders if total_orders > 0 else 0

            # Process daily sales with proper date handling
            daily_sales_dict = {}
            dates = []
            
            for order in orders:
                # Convert string to datetime object
                order_date = datetime.strptime(order.created_at, "%Y-%m-%dT%H:%M:%S%z").date()
                daily_sales_dict[order_date] = daily_sales_dict.get(order_date, 0) + float(order.total_price)
                dates.append(order_date)

            # Sort dates and get corresponding sales
            dates = sorted(list(set(dates)))
            daily_sales = [daily_sales_dict[date] for date in dates]

            # Process products
            top_products_data = []
            for product in products[:10]:  # Top 10 products
                variants = product.variants
                if variants:
                    variant = variants[0]
                    top_products_data.append({
                        'title': product.title,
                        'price': float(variant.price),
                        'inventory': variant.inventory_quantity or 0
                    })

            # Get sales by category
            sales_by_category = self.process_sales_by_category(orders, products)
            
            # Get sales by channel
            sales_by_channel = self.process_sales_by_channel(orders)

            # Prepare store data
            store_data = {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'avg_order_value': avg_order_value,
                'active_customers': len(customers),
                'daily_sales': daily_sales,
                'dates': [d.strftime('%Y-%m-%d') for d in dates],  # Convert dates to strings
                'top_products': pd.DataFrame(top_products_data),
                'sales_by_category': sales_by_category,
                'sales_by_channel': sales_by_channel
            }

            # Add AI-generated insights
            ai_insights = self.generate_ai_insights(store_data)
            store_data.update(ai_insights)

            return store_data

        except Exception as e:
            logger.error(f"Error getting store data: {str(e)}")
            raise

    def process_sales_by_category(self, orders, products):
        """Process sales by product category."""
        category_sales = {}
        product_map = {str(p.id): p.product_type for p in products}
        
        for order in orders:
            for item in order.line_items:
                category = product_map.get(str(item.product_id), 'Uncategorized')
                if category == '':
                    category = 'Uncategorized'
                category_sales[category] = category_sales.get(category, 0) + float(item.price)

        return pd.DataFrame([
            {'category': cat, 'sales': sales}
            for cat, sales in category_sales.items()
        ])

    def process_sales_by_channel(self, orders):
        """Process sales by channel."""
        channel_sales = {}
        for order in orders:
            channel = order.source_name or 'Direct'
            channel_sales[channel] = channel_sales.get(channel, 0) + float(order.total_price)

        return pd.DataFrame([
            {'channel': channel, 'sales': sales}
            for channel, sales in channel_sales.items()
        ])

    def generate_ai_insights(self, store_data):
        """Generate AI-powered insights using OpenAI."""
        try:
            # Prepare data for analysis with a more structured prompt
            analysis_prompt = f"""Please analyze this e-commerce store data and provide specific insights and recommendations in the following JSON format:
{{
    "customer_insights": [
        "Key insight about customer behavior 1",
        "Key insight about customer behavior 2",
        "Key insight about customer behavior 3"
    ],
    "product_recommendations": [
        "Specific product strategy 1",
        "Specific product strategy 2",
        "Specific product strategy 3"
    ],
    "recommendations": {{
        "Sales Optimization": [
            "Specific sales improvement tactic 1",
            "Specific sales improvement tactic 2"
        ],
        "Inventory Management": [
            "Specific inventory strategy 1",
            "Specific inventory strategy 2"
        ],
        "Marketing Strategies": [
            "Specific marketing tactic 1",
            "Specific marketing tactic 2"
        ],
        "Customer Experience": [
            "Specific customer experience improvement 1",
            "Specific customer experience improvement 2"
        ],
        "Operational Efficiency": [
            "Specific operational improvement 1",
            "Specific operational improvement 2"
        ]
    }}
}}

Store Metrics:
- Total Sales: ${store_data['total_sales']:,.2f}
- Total Orders: {store_data['total_orders']}
- Average Order Value: ${store_data['avg_order_value']:,.2f}
- Active Customers: {store_data['active_customers']}

Based on these metrics, provide actionable insights and recommendations in the exact JSON format shown above.
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert e-commerce analyst. Provide insights in the exact JSON format requested. Ensure the response is valid JSON."
                    },
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}  # Ensure JSON response
            )

            # Parse the AI response with error handling
            try:
                ai_insights = json.loads(response.choices[0].message.content)
                logger.info("Successfully generated AI insights")
                return ai_insights
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {e}")
                return self.get_default_insights()

        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return self.get_default_insights()

    def get_default_insights(self):
        """Return default insights when AI generation fails."""
        return {
            'customer_insights': [
                "Analyze customer purchase frequency",
                "Review customer lifetime value",
                "Monitor customer retention rates"
            ],
            'product_recommendations': [
                "Review top-performing products",
                "Optimize inventory levels",
                "Consider product bundling opportunities"
            ],
            'recommendations': {
                "Sales Optimization": [
                    "Analyze peak sales periods",
                    "Review pricing strategies"
                ],
                "Inventory Management": [
                    "Monitor stock levels",
                    "Implement inventory alerts"
                ],
                "Marketing Strategies": [
                    "Segment customer base",
                    "Develop targeted campaigns"
                ],
                "Customer Experience": [
                    "Gather customer feedback",
                    "Optimize checkout process"
                ],
                "Operational Efficiency": [
                    "Streamline fulfillment process",
                    "Review shipping options"
                ]
            }
        }

    # ----------------------------------------------
    # Stub implementations for data retrieval below.
    # Replace these with your actual implementations.
    def get_total_sales(self):
        return 10000.0

    def get_total_orders(self):
        return 120

    def calculate_avg_order_value(self):
        orders = self.get_total_orders()
        return self.get_total_sales() / orders if orders else 0

    def get_active_customers(self):
        return 80

    def get_daily_sales(self):
        return [1000, 1200, 1100, 900, 1300]

    def get_sales_dates(self):
        return ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]

    def get_top_products(self):
        # Return a dummy DataFrame for demonstration
        return pd.DataFrame([
            {'title': 'Product A', 'price': 20.0, 'inventory': 50},
            {'title': 'Product B', 'price': 35.0, 'inventory': 30}
        ])

    def generate_product_recommendations(self):
        return ["Restock Product A", "Consider promotions for Product B"]

    def get_sales_by_category(self):
        # Return a dummy DataFrame for demonstration
        return pd.DataFrame({
            'category': ['Category A', 'Category B', 'Category C'],
            'sales': [4000, 3500, 2500]
        })

    def get_sales_by_channel(self):
        # Return a dummy DataFrame for demonstration
        return pd.DataFrame({
            'channel': ['Online', 'Retail', 'Mobile'],
            'sales': [5000, 3000, 2000]
        })

    def get_customer_segments(self):
        return pd.DataFrame({
            'segment': ['New', 'Returning', 'VIP'],
            'count': [70, 40, 10]
        })

    def generate_customer_insights(self):
        return [
            "60% of customers are repeat buyers",
            "High engagement during holiday seasons"
        ]

    def generate_recommendations(self):
        return {
            "Sales Optimization": ["Increase marketing spend during peak times"],
            "Inventory Management": ["Automate reorder thresholds"],
            "Marketing Strategies": ["Launch targeted email campaigns"],
            "Customer Experience": ["Enhance mobile site navigation"],
            "Operational Efficiency": ["Streamline order fulfillment process"]
        }

def validate_shopify_credentials(access_token, shop_url):
    """Validate Shopify credentials by attempting to fetch store data."""
    try:
        # Format shop URL
        if not shop_url.startswith('https://'):
            shop_url = f"https://{shop_url}"
        if not shop_url.endswith('.myshopify.com'):
            shop_url = f"{shop_url}.myshopify.com"

        # Initialize Shopify API
        shopify.Session.setup(api_key=os.getenv('SHOPIFY_API_KEY'), secret=os.getenv('SHOPIFY_API_SECRET'))
        session = shopify.Session(shop_url, '2024-01', access_token)
        shopify.ShopifyResource.activate_session(session)

        # Test the connection
        shop = shopify.Shop.current()
        if shop:
            return True, f"Successfully connected to {shop.name}!"
        return False, "Unable to connect to store"

    except Exception as e:
        if '401' in str(e):
            return False, "Invalid API credentials. Please check your access token."
        elif '404' in str(e):
            return False, "Store not found. Please check your shop URL."
        else:
            return False, f"Connection error: {str(e)}"