import os
import ssl
import certifi
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util.retry import Retry
from sqlalchemy.orm import Session
import pandas as pd
from models import StoreAnalytics, ProductAnalytics, OptimizationType
from utils.error_handler import handle_api_error
from dotenv import load_dotenv
import json
from database import get_db_session  # Ensure this is imported
import numpy as np
from sklearn.preprocessing import StandardScaler
from prophet import Prophet
import openai
from requests.exceptions import RequestException

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class DataConnector:
    def __init__(self, shop_url: str, access_token: str):
        """Initialize the data connector with proper authentication"""
        self.shop_url = shop_url.rstrip('/')  # Remove trailing slash if present
        self.access_token = access_token
        self.headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        self.base_url = f"https://{shop_url}/admin/api/2024-01"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Verify connection on initialization
        self._verify_connection()

    def _verify_connection(self):
        """Verify API connection and authentication"""
        try:
            # Test connection with a simple API call
            response = self.session.get(f"{self.base_url}/shop.json")
            response.raise_for_status()
            logger.info("Successfully connected to Shopify API")
        except RequestException as e:
            logger.error(f"Failed to connect to Shopify API: {str(e)}")
            if e.response and e.response.status_code == 401:
                logger.error("Authentication failed. Please check your access token.")
            raise

    def _get_products(self) -> List[Dict]:
        """Fetch products from Shopify API with proper error handling"""
        try:
            products = []
            page_info = None
            
            while True:
                # Prepare request parameters
                params = {'limit': 250}  # Maximum allowed by Shopify
                if page_info:
                    params['page_info'] = page_info
                
                # Make API request
                response = self.session.get(
                    f"{self.base_url}/products.json",
                    params=params
                )
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                if not data or 'products' not in data:
                    break
                
                products.extend(data['products'])
                
                # Check for pagination
                link_header = response.headers.get('Link')
                if not link_header or 'next' not in link_header:
                    break
                
                # Extract page_info for next request
                page_info = self._extract_page_info(link_header)
            
            logger.info(f"Successfully fetched {len(products)} products")
            return products
            
        except RequestException as e:
            logger.error(f"Error fetching products: {str(e)}")
            if e.response and e.response.status_code == 401:
                logger.error("Authentication failed. Please check your access token.")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching products: {str(e)}")
            return []

    def _get_orders(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch orders from Shopify API with proper error handling"""
        try:
            orders = []
            page_info = None
            
            while True:
                # Prepare request parameters
                params = {
                    'limit': 250,
                    'created_at_min': start_date.isoformat(),
                    'created_at_max': end_date.isoformat(),
                    'status': 'any'
                }
                if page_info:
                    params['page_info'] = page_info
                
                # Make API request
                response = self.session.get(
                    f"{self.base_url}/orders.json",
                    params=params
                )
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                if not data or 'orders' not in data:
                    break
                
                orders.extend(data['orders'])
                
                # Check for pagination
                link_header = response.headers.get('Link')
                if not link_header or 'next' not in link_header:
                    break
                
                # Extract page_info for next request
                page_info = self._extract_page_info(link_header)
            
            logger.info(f"Successfully fetched {len(orders)} orders")
            return orders
            
        except RequestException as e:
            logger.error(f"Error fetching orders: {str(e)}")
            if e.response and e.response.status_code == 401:
                logger.error("Authentication failed. Please check your access token.")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching orders: {str(e)}")
            return []

    def _extract_page_info(self, link_header: str) -> Optional[str]:
        """Extract page_info from Link header"""
        try:
            if 'next' not in link_header:
                return None
            
            next_link = [l for l in link_header.split(', ') if 'rel="next"' in l][0]
            return next_link.split('page_info=')[1].split('>')[0]
        except Exception:
            return None

    def _generate_predictions(self, orders: List[Dict]) -> Dict:
        """Generate sales predictions with proper error handling"""
        try:
            if not orders:
                logger.warning("No orders available for predictions")
                return self._get_empty_predictions()
            
            # Prepare data for Prophet
            daily_sales = self._get_daily_sales(orders)
            if not daily_sales:
                return self._get_empty_predictions()
            
            df = pd.DataFrame(daily_sales)
            df.columns = ['ds', 'y']
            
            # Configure Prophet
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.95
            )
            
            # Fit model and generate forecast
            model.fit(df)
            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)
            
            return {
                'dates': forecast['ds'].tail(30).dt.strftime('%Y-%m-%d').tolist(),
                'values': forecast['yhat'].tail(30).round(2).tolist(),
                'lower_bound': forecast['yhat_lower'].tail(30).round(2).tolist(),
                'upper_bound': forecast['yhat_upper'].tail(30).round(2).tolist()
            }
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            return self._get_empty_predictions()

    def _get_empty_predictions(self) -> Dict:
        """Return empty prediction structure"""
        return {
            'dates': [],
            'values': [],
            'lower_bound': [],
            'upper_bound': []
        }

    @handle_api_error
    def get_store_analytics(self, days: int = 30, goal: str = None) -> Dict:
        """Fetch store analytics data with predictions and categories"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Initialize empty data structures
            orders = []
            products = []
            
            try:
                # Fetch orders and products with error handling
                orders = self._get_orders(start_date, end_date) or []
                products = self._get_products() or []
            except Exception as e:
                logger.error(f"API Error: {str(e)}")
                # Continue with empty data rather than failing
            
            # Calculate basic metrics with safe defaults
            total_orders = len(orders)
            total_sales = float(sum(float(order.get('total_price', 0)) for order in orders))
            total_cost = float(sum(float(order.get('total_cost', 0)) for order in orders))
            average_order_value = float(total_sales / total_orders if total_orders > 0 else 0)
            
            # Calculate previous period metrics
            previous_start = start_date - timedelta(days=days)
            previous_end = start_date
            try:
                previous_orders = self._get_orders(previous_start, previous_end) or []
            except Exception:
                previous_orders = []
            
            previous_sales = float(sum(float(order.get('total_price', 0)) for order in previous_orders))
            previous_cost = float(sum(float(order.get('total_cost', 0)) for order in previous_orders))
            
            # Calculate financial metrics with safe defaults
            roi = float(((total_sales - total_cost) / total_cost * 100) if total_cost > 0 else 0)
            previous_roi = float(((previous_sales - previous_cost) / previous_cost * 100) if previous_cost > 0 else 0)
            roi_change = float(roi - previous_roi)
            
            # Calculate revenue metrics
            revenue_change = float(total_sales - previous_sales)
            revenue_change_percentage = float((revenue_change / previous_sales * 100) if previous_sales > 0 else 0)
            
            # Safe conversion metrics calculation
            conversion_metrics = {
                'total_sessions': max(total_orders * 20, 1),  # Ensure non-zero denominator
                'conversion_rate': 0.0,
                'previous_sessions': max(len(previous_orders) * 20, 1),
                'previous_conversion': 0.0,
                'conversion_change': 0.0,
                'sessions_change': 0
            }
            
            try:
                conversion_metrics = self._calculate_conversion_metrics(total_orders, len(previous_orders))
            except Exception as e:
                logger.warning(f"Error calculating conversion metrics: {str(e)}")
            
            analytics_data = {
                # Current period metrics
                'total_sales': float(total_sales),
                'total_orders': int(total_orders),
                'average_order_value': float(average_order_value),
                'conversion_rate': float(conversion_metrics['conversion_rate']),
                'total_sessions': int(conversion_metrics['total_sessions']),
                'roi': float(roi),
                'profit_margin': float((total_sales - total_cost) / total_sales * 100 if total_sales > 0 else 0),
                
                # Changes and impacts
                'revenue_change': float(revenue_change),
                'revenue_change_percentage': float(revenue_change_percentage),
                'roi_change': float(roi_change),
                'conversion_change': float(conversion_metrics['conversion_change']),
                
                # Previous period metrics
                'previous_sales': float(previous_sales),
                'previous_orders': int(len(previous_orders)),
                'previous_sessions': int(conversion_metrics['previous_sessions']),
                'previous_conversion': float(conversion_metrics['previous_conversion']),
                
                # Category performance
                'category_performance': self._calculate_category_performance(orders, products),
                
                # Time series data
                'daily_sales': self._get_daily_sales(orders),
                'weekly_sales': self._get_weekly_sales(orders),
                
                # Predictions
                'predictions': self._generate_predictions(orders),
                
                # AI Insights and Recommendations
                'ai_insights': self._generate_ai_insights(
                    total_sales=total_sales,
                    total_orders=total_orders,
                    roi=roi,
                    category_performance=self._calculate_category_performance(orders, products),
                    goal=goal
                ),
                'optimization_recommendations': self._generate_optimization_recommendations(
                    conversion_metrics,
                    self._calculate_category_performance(orders, products),
                    roi
                )
            }
            
            # Store in database
            try:
                self._store_analytics(analytics_data)
            except Exception as e:
                logger.error(f"Error storing analytics: {str(e)}")
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error fetching store analytics: {str(e)}")
            return self._get_empty_analytics()

    def _get_analytics(self) -> Dict:
        """Fetch analytics data from Shopify"""
        try:
            # Try to get analytics from Shopify Analytics API
            response = self.session.get(f"{self.base_url}/reports/analytics.json")
            if response.status_code == 200:
                return response.json()
            
            # If analytics API is not available, estimate from orders
            logger.warning("Could not fetch analytics data, using estimates")
            return {
                'total_sessions': None,  # Will be calculated based on orders
                'previous_sessions': None  # Will be calculated based on previous orders
            }
        except Exception as e:
            logger.error(f"Error fetching analytics: {str(e)}")
            return {
                'total_sessions': None,
                'previous_sessions': None
            }

    def _get_daily_sales(self, orders: List[Dict]) -> List[Dict]:
        """Calculate daily sales with proper data structure"""
        try:
            if not orders:
                return []
            
            # Convert orders to DataFrame
            df = pd.DataFrame([
                {
                    'date': pd.to_datetime(order['created_at']).date(),
                    'sales': float(order['total_price'])
                }
                for order in orders
            ])
            
            # Group by date and sum sales
            daily_sales = df.groupby('date')['sales'].sum().reset_index()
            
            # Convert to list of dictionaries with proper structure
            return [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'value': float(sales)  # Ensure float type
                }
                for date, sales in zip(daily_sales['date'], daily_sales['sales'])
            ]
        except Exception as e:
            logger.error(f"Error calculating daily sales: {str(e)}")
            return []

    def _get_weekly_sales(self, orders: List[Dict]) -> List[Dict]:
        """Calculate weekly sales with proper data structure"""
        try:
            if not orders:
                return []
            
            # Convert orders to DataFrame
            df = pd.DataFrame([
                {
                    'date': pd.to_datetime(order['created_at']),
                    'sales': float(order['total_price'])
                }
                for order in orders
            ])
            
            # Group by week and sum sales
            df['week'] = df['date'].dt.strftime('%Y-%U')
            weekly_sales = df.groupby('week')['sales'].sum().reset_index()
            
            # Convert week numbers to dates (start of week)
            weekly_sales['week_start'] = weekly_sales['week'].apply(
                lambda x: datetime.strptime(f"{x}-1", "%Y-%U-%w")
            )
            
            # Convert to list of dictionaries with proper structure
            return [
                {
                    'date': week_start.strftime('%Y-%m-%d'),
                    'value': float(sales)  # Ensure float type
                }
                for week_start, sales in zip(weekly_sales['week_start'], weekly_sales['sales'])
            ]
        except Exception as e:
            logger.error(f"Error calculating weekly sales: {str(e)}")
            return []

    def _get_empty_analytics(self) -> Dict:
        """Return empty analytics data structure with correct types"""
        return {
            'total_sales': 0.0,
            'total_orders': 0,
            'average_order_value': 0.0,
            'conversion_rate': 0.0,
            'total_sessions': 0,
            'roi': 0.0,
            'profit_margin': 0.0,
            'previous_roi': 0.0,
            'roi_change': 0.0,
            'revenue_change': 0.0,
            'revenue_change_percentage': 0.0,
            'revenue_impact': 0.0,
            'conversion_change': 0.0,
            'previous_sales': 0.0,
            'previous_orders': 0,
            'previous_sessions': 0,
            'previous_conversion': 0.0,
            'daily_sales': [],
            'weekly_sales': [],
            'category_performance': {},
            'predictions': {
                'dates': [],
                'values': [],
                'lower_bound': [],
                'upper_bound': []
            },
            'ai_insights': [],
            'optimization_recommendations': []
        }

    def _store_analytics(self, analytics_data: Dict):
        """Store analytics data in database"""
        try:
            with get_db_session() as db:  # Use the context manager
                store_analytics = StoreAnalytics(
                    date=datetime.utcnow(),
                    total_sales=analytics_data['total_sales'],
                    total_orders=analytics_data['total_orders'],
                    average_order_value=analytics_data['average_order_value'],
                    conversion_rate=analytics_data['conversion_rate'],
                    total_sessions=analytics_data['total_sessions']
                )
                db.add(store_analytics)
                db.commit()
        except Exception as e:
            logger.error(f"Error storing analytics: {str(e)}")
            # No need to call db.rollback() here, as the context manager handles it
            raise

    def __del__(self):
        """Cleanup"""
        try:
            self.session.close()
        except:
            pass

    def _calculate_category_performance(self, orders: List[Dict], products: List[Dict]) -> Dict:
        """Calculate performance metrics by category"""
        try:
            category_data = {}
            for order in orders:
                for item in order.get('line_items', []):
                    product_id = item.get('product_id')
                    product = next((p for p in products if p['id'] == product_id), None)
                    if product:
                        category = product.get('product_type', 'Uncategorized')
                        if category not in category_data:
                            category_data[category] = {
                                'sales': 0.0,
                                'orders': 0,
                                'items_sold': 0
                            }
                        category_data[category]['sales'] += float(item['price']) * item['quantity']
                        category_data[category]['orders'] += 1
                        category_data[category]['items_sold'] += item['quantity']
            
            return category_data
        except Exception as e:
            logger.error(f"Error calculating category performance: {str(e)}")
            return {}

    def _generate_ai_insights(self, **kwargs) -> List[Dict]:
        """Generate AI-powered insights based on analytics data and custom goal"""
        try:
            insights = []
            goal = kwargs.get('goal', 'revenue_growth')
            
            # Base metrics for analysis
            metrics = {
                'total_sales': kwargs['total_sales'],
                'roi': kwargs['roi'],
                'conversion_rate': kwargs.get('conversion_rate', 0),
                'category_performance': kwargs.get('category_performance', {})
            }
            
            # Goal-specific insights
            goal_insights = self._get_goal_specific_insights(goal, metrics)
            insights.extend(goal_insights)
            
            # Performance insights
            if metrics['total_sales'] > 0:
                insights.append({
                    'type': 'revenue',
                    'title': 'Revenue Performance',
                    'description': f"Current ROI is {metrics['roi']:.1f}%",
                    'recommendation': self._get_roi_recommendation(metrics['roi'])
                })
            
            # Category insights
            category_data = metrics['category_performance']
            if category_data:
                top_category = max(category_data.items(), key=lambda x: x[1]['sales'])
                insights.append({
                    'type': 'category',
                    'title': 'Category Performance',
                    'description': f"Best performing category: {top_category[0]}",
                    'recommendation': f"Focus marketing efforts on {top_category[0]}"
                })
            
            return insights
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return []

    def _get_goal_specific_insights(self, goal: str, metrics: Dict) -> List[Dict]:
        """Generate goal-specific insights"""
        goal_insights = []
        
        if goal == 'revenue_growth':
            if metrics['total_sales'] > 0:
                goal_insights.append({
                    'type': 'goal',
                    'title': 'Revenue Growth Strategy',
                    'description': 'Analysis of revenue growth potential',
                    'recommendation': self._get_revenue_growth_recommendations(metrics)
                })
                
        elif goal == 'conversion_optimization':
            if metrics.get('conversion_rate'):
                goal_insights.append({
                    'type': 'goal',
                    'title': 'Conversion Optimization',
                    'description': f"Current conversion rate: {metrics['conversion_rate']:.1f}%",
                    'recommendation': self._get_conversion_recommendations(metrics['conversion_rate'])
                })
                
        elif goal == 'inventory_optimization':
            if metrics.get('category_performance'):
                goal_insights.append({
                    'type': 'goal',
                    'title': 'Inventory Optimization',
                    'description': 'Category-based inventory analysis',
                    'recommendation': self._get_inventory_recommendations(metrics['category_performance'])
                })
        
        return goal_insights

    def _get_revenue_growth_recommendations(self, metrics: Dict) -> str:
        """Generate revenue growth recommendations"""
        if metrics['roi'] < 20:
            return "Focus on improving ROI through cost optimization and pricing strategy"
        elif metrics['conversion_rate'] < 3:
            return "Prioritize conversion rate optimization to drive revenue growth"
        else:
            return "Expand marketing efforts for top-performing categories"

    def _get_conversion_recommendations(self, conversion_rate: float) -> str:
        """Generate conversion optimization recommendations"""
        if conversion_rate < 1:
            return "Critical: Implement urgent conversion rate optimization strategies"
        elif conversion_rate < 3:
            return "Optimize checkout process and improve product pages"
        else:
            return "Fine-tune existing conversion strategies"

    def _get_inventory_recommendations(self, category_performance: Dict) -> str:
        """Generate inventory optimization recommendations"""
        try:
            top_categories = sorted(
                category_performance.items(),
                key=lambda x: x[1]['sales'],
                reverse=True
            )[:3]
            
            recommendations = [
                f"Optimize inventory for top category: {top_categories[0][0]}",
                "Review stock levels for seasonal trends",
                "Consider bulk purchasing for high-volume categories"
            ]
            
            return " | ".join(recommendations)
        except Exception:
            return "Insufficient data for inventory recommendations"

    def _get_roi_recommendation(self, roi: float) -> str:
        """Generate ROI-based recommendations"""
        if roi < 10:
            return "Critical: Review pricing strategy and cost structure"
        elif roi < 20:
            return "Consider optimizing operational costs and marketing spend"
        else:
            return "Maintain current performance and explore scaling opportunities"

    def _calculate_conversion_metrics(self, current_orders: int, previous_orders: int) -> Dict:
        """Calculate conversion metrics with safe defaults"""
        try:
            # Ensure we have positive values for calculations
            current_orders = max(current_orders, 0)
            previous_orders = max(previous_orders, 0)
            
            # Estimate sessions (assuming 5% conversion rate as default)
            total_sessions = max(current_orders * 20, 1)  # Ensure non-zero denominator
            previous_sessions = max(previous_orders * 20, 1)
            
            # Calculate conversion rates
            conversion_rate = float((current_orders / total_sessions * 100) if total_sessions > 0 else 0)
            previous_conversion = float((previous_orders / previous_sessions * 100) if previous_sessions > 0 else 0)
            
            # Calculate changes
            conversion_change = float(conversion_rate - previous_conversion)
            sessions_change = int(total_sessions - previous_sessions)
            
            return {
                'total_sessions': int(total_sessions),
                'conversion_rate': float(conversion_rate),
                'previous_sessions': int(previous_sessions),
                'previous_conversion': float(previous_conversion),
                'conversion_change': float(conversion_change),
                'sessions_change': int(sessions_change)
            }
        except Exception as e:
            logger.error(f"Error calculating conversion metrics: {str(e)}")
            return {
                'total_sessions': 1,
                'conversion_rate': 0.0,
                'previous_sessions': 1,
                'previous_conversion': 0.0,
                'conversion_change': 0.0,
                'sessions_change': 0
            }

    def _generate_optimization_recommendations(self, conversion_metrics: Dict, 
                                            category_performance: Dict, roi: float) -> List[Dict]:
        """Generate optimization recommendations"""
        try:
            recommendations = []
            
            # Conversion rate optimization
            if conversion_metrics['conversion_rate'] < 3.0:
                recommendations.append({
                    'type': OptimizationType.CONVERSION.value,
                    'title': 'Improve Conversion Rate',
                    'description': 'Current conversion rate is below industry average',
                    'impact': 'High',
                    'actions': ['Optimize checkout process', 'Add trust badges', 'Improve product pages']
                })
            
            # ROI optimization
            if roi < 20.0:
                recommendations.append({
                    'type': OptimizationType.PRICING.value,
                    'title': 'Improve ROI',
                    'description': 'Current ROI is below target',
                    'impact': 'High',
                    'actions': ['Review pricing strategy', 'Optimize inventory', 'Reduce costs']
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {str(e)}")
            return [] 