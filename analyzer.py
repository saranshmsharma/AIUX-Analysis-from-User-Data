from shopify_client import ShopifyClient
from models import ABTest, StoreAnalytics, ProductAnalytics
from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta

class ShopAnalyzer:
    def __init__(self, shopify_client: ShopifyClient):
        self.shopify_client = shopify_client

    def analyze_store_performance(self) -> Dict:
        """Analyze overall store performance"""
        try:
            analytics_data = self.shopify_client.get_analytics_data()
            orders = self.shopify_client.get_orders()
            products = self.shopify_client.get_products()
            
            if not analytics_data:
                return None

            # Calculate key metrics
            total_sales = analytics_data['total_sales']
            total_orders = analytics_data['total_orders']
            avg_order_value = analytics_data['average_order_value']
            
            # Calculate conversion metrics
            conversion_rate = (total_orders / 100) if total_orders > 0 else 0
            
            # Product performance
            product_performance = self.analyze_product_performance(products)
            
            # Sales trends
            sales_trends = self.analyze_sales_trends(orders)
            
            return {
                'total_sales': total_sales,
                'total_orders': total_orders,
                'average_order_value': avg_order_value,
                'conversion_rate': conversion_rate,
                'top_products': product_performance['top_products'],
                'sales_trends': sales_trends,
                'raw_data': {
                    'orders': orders,
                    'products': products
                }
            }
            
        except Exception as e:
            print(f"Error analyzing store performance: {str(e)}")
            return None

    def analyze_sales_trends(self, orders: List[Dict] = None) -> pd.DataFrame:
        """Analyze sales trends over time"""
        try:
            if orders is None:
                orders = self.shopify_client.get_orders()
            
            # Convert orders to DataFrame
            df = pd.DataFrame(orders)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['total_price'] = pd.to_numeric(df['total_price'])
            
            # Daily sales
            daily_sales = df.groupby(df['created_at'].dt.date)['total_price'].sum().reset_index()
            daily_sales.columns = ['date', 'daily_sales']
            
            # Weekly sales
            weekly_sales = df.groupby(pd.Grouper(key='created_at', freq='W'))['total_price'].sum().reset_index()
            weekly_sales.columns = ['date', 'weekly_sales']
            
            return {
                'daily_sales': daily_sales.to_dict('records'),
                'weekly_sales': weekly_sales.to_dict('records')
            }
            
        except Exception as e:
            print(f"Error analyzing sales trends: {str(e)}")
            return None

    def analyze_product_performance(self, products: List[Dict]) -> Dict:
        """Analyze product performance"""
        try:
            # Convert to DataFrame for analysis
            product_data = []
            for product in products:
                for variant in product['variants']:
                    product_data.append({
                        'product_id': product['id'],
                        'title': product['title'],
                        'price': float(variant['price']),
                        'inventory': variant['inventory_quantity']
                    })
            
            df = pd.DataFrame(product_data)
            
            # Get top products by price
            top_products = df.nlargest(5, 'price')[['title', 'price']].to_dict('records')
            
            return {
                'top_products': top_products
            }
            
        except Exception as e:
            print(f"Error analyzing product performance: {str(e)}")
            return None

    def get_store_metrics(self) -> Dict:
        """Get key store metrics"""
        try:
            performance = self.analyze_store_performance()
            trends = self.analyze_sales_trends()
            
            return {
                **performance,
                'sales_trends': trends
            }
            
        except Exception as e:
            print(f"Error getting store metrics: {str(e)}")
            return None

    def get_key_metrics(self):
        orders_df = self.data_processor.get_orders_df()
        products_df = self.data_processor.get_products_df()

        total_revenue = orders_df['total_price'].sum()
        avg_order_value = orders_df['total_price'].mean()
        total_orders = len(orders_df)
        total_products = len(products_df)

        return {
            'Total Revenue': f"${total_revenue:,.2f}",
            'Average Order Value': f"${avg_order_value:,.2f}",
            'Total Orders': total_orders,
            'Total Products': total_products
        }

    def get_products_list(self):
        products_df = self.data_processor.get_products_df()
        return products_df['title'].tolist()

    def get_product_id(self, product_title):
        """Get product ID by title"""
        products_df = self.data_processor.get_products_df()
        product = products_df[products_df['title'] == product_title].iloc[0]
        return product.name

    def _calculate_daily_sales(self, product_orders):
        if len(product_orders) == 0:
            return pd.DataFrame()

        daily_sales = product_orders.groupby(
            pd.to_datetime(product_orders['created_at']).dt.date
        )['total_price'].agg(['sum', 'count']).reset_index()

        daily_sales.columns = ['date', 'revenue', 'orders']
        return daily_sales