import re
from typing import Tuple, Dict, Any
from datetime import datetime

class ValidationError(Exception):
    pass

def validate_shopify_url(url: str) -> Tuple[bool, str]:
    """Enhanced Shopify URL validation"""
    if not url:
        return False, "Shop URL is required"
    
    url = url.strip().lower()
    
    # Basic format check
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*\.myshopify\.com$'
    if not re.match(pattern, url):
        return False, "Invalid URL format. Use: store-name.myshopify.com"
    
    # Length check
    if len(url) < 14 or len(url) > 100:
        return False, "Shop URL length is invalid"
    
    # Subdomain check
    subdomain = url.split('.')[0]
    if len(subdomain) < 3:
        return False, "Shop name is too short"
    
    # Reserved words check
    reserved_words = ['admin', 'shopify', 'login', 'ssl']
    if subdomain in reserved_words:
        return False, "Invalid shop name: contains reserved word"
    
    return True, "Valid shop URL"

def validate_access_token(token: str) -> Tuple[bool, str]:
    """Enhanced access token validation"""
    if not token:
        return False, "Access token is required"
    
    token = token.strip()
    
    # Basic format check
    pattern = r'^shpat_[a-zA-Z0-9]{32,}$'
    if not re.match(pattern, token):
        return False, "Invalid token format. Should start with 'shpat_'"
    
    # Length check
    if len(token) < 38 or len(token) > 100:
        return False, "Token length is invalid"
    
    return True, "Valid access token"

def validate_business_goal(goal: str) -> Tuple[bool, str]:
    """Validate business goal format and content"""
    if not goal:
        return False, "Business goal is required"
    
    goal = goal.strip()
    
    # Length check
    if len(goal) < 10:
        return False, "Goal description is too short"
    if len(goal) > 200:
        return False, "Goal description is too long"
    
    # Check for measurable metrics
    metrics_keywords = ['increase', 'decrease', 'reduce', 'improve', 'grow', 'achieve']
    has_metric = any(keyword in goal.lower() for keyword in metrics_keywords)
    if not has_metric:
        return False, "Goal should include measurable metrics"
    
    # Check for timeframe
    timeframe_keywords = ['day', 'week', 'month', 'year', 'quarter']
    has_timeframe = any(keyword in goal.lower() for keyword in timeframe_keywords)
    if not has_timeframe:
        return False, "Goal should include a timeframe"
    
    return True, "Valid business goal"

def validate_analytics_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate analytics data structure and values"""
    required_fields = ['total_sales', 'total_orders', 'average_order_value', 'conversion_rate']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
        
        # Validate numeric values
        if not isinstance(data[field], (int, float)):
            return False, f"Invalid value type for {field}"
        
        # Validate ranges
        if data[field] < 0:
            return False, f"Negative value not allowed for {field}"
    
    return True, "Valid analytics data"

def validate_date_range(start_date: str, end_date: str) -> Tuple[bool, str]:
    """Validate date range format and logic"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        if end < start:
            return False, "End date cannot be before start date"
        
        if (end - start).days > 365:
            return False, "Date range cannot exceed 1 year"
        
        return True, "Valid date range"
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD" 