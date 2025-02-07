import logging
import traceback
from typing import Optional, Dict, Any
import streamlit as st
from functools import wraps
from datetime import datetime
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception class for application errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or 'UNKNOWN_ERROR'
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(AppError):
    """Database related errors"""
    pass

class APIError(AppError):
    """API related errors"""
    pass

class ValidationError(AppError):
    """Data validation errors"""
    pass

def error_handler(error_type: str = None):
    """Decorator for handling errors in functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_details = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'function': func.__name__,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'traceback': traceback.format_exc()
                }
                
                logger.error(f"Error in {func.__name__}: {str(e)}")
                logger.debug(f"Error details: {error_details}")
                
                # Log error to file
                log_error_to_file(error_details)
                
                # Show appropriate error message in UI
                show_error_message(error_type or 'general', str(e))
                
                return None
        return wrapper
    return decorator

def log_error_to_file(error_details: Dict[str, Any]) -> None:
    """Log error details to a JSON file"""
    try:
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, 'error_log.json')
        
        existing_logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                existing_logs = json.load(f)
                
        existing_logs.append(error_details)
        
        with open(log_file, 'w') as f:
            json.dump(existing_logs, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error logging to file: {str(e)}")

def show_error_message(error_type: str, message: str) -> None:
    """Show appropriate error message in Streamlit UI"""
    error_messages = {
        'database': {
            'title': '🔴 Database Error',
            'suggestion': 'Please check your database connection and try again.'
        },
        'api': {
            'title': '🔴 API Error',
            'suggestion': 'Please check your API credentials and try again.'
        },
        'validation': {
            'title': '🔶 Validation Error',
            'suggestion': 'Please check your input data and try again.'
        },
        'general': {
            'title': '⚠️ Error',
            'suggestion': 'An unexpected error occurred. Please try again.'
        }
    }
    
    error_config = error_messages.get(error_type, error_messages['general'])
    
    st.error(f"{error_config['title']}: {message}")
    st.info(error_config['suggestion'])
    
    if st.button("Show Error Details"):
        st.code(traceback.format_exc())

def handle_api_error(func):
    """Specific decorator for API-related functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise APIError(f"API Error: {str(e)}", error_code='API_ERROR')
    return wrapper

def handle_validation_error(func):
    """Specific decorator for data validation functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise ValidationError(f"Validation Error: {str(e)}", error_code='VALIDATION_ERROR')
    return wrapper

def init_error_handling():
    """Initialize error handling for the application"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Set up logging configuration
    logging.basicConfig(
        filename='logs/app.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add streamlit exception handling
    st.set_option('client.showErrorDetails', True) 