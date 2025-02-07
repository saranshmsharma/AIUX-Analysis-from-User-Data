import streamlit as st
from typing import Optional, Callable, Any
import traceback
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorRecovery:
    def __init__(self):
        self.error_log_file = "error_logs.json"
        self.max_retries = 3
        
    def log_error(self, error: Exception, context: dict) -> None:
        """Log error details to file"""
        try:
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "context": context
            }
            
            # Load existing logs
            existing_logs = []
            if os.path.exists(self.error_log_file):
                with open(self.error_log_file, 'r') as f:
                    existing_logs = json.load(f)
            
            # Add new error
            existing_logs.append(error_data)
            
            # Save updated logs
            with open(self.error_log_file, 'w') as f:
                json.dump(existing_logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    def handle_error(self, error: Exception, context: dict) -> None:
        """Handle error and suggest recovery actions"""
        self.log_error(error, context)
        
        error_type = type(error).__name__
        
        if error_type == "ConnectionError":
            st.error("Connection failed. Please check your internet connection.")
            if st.button("Retry Connection"):
                st.rerun()
                
        elif error_type == "ValidationError":
            st.error(f"Validation Error: {str(error)}")
            st.info("Please check your input and try again.")
            
        elif error_type == "AuthenticationError":
            st.error("Authentication failed. Please check your credentials.")
            if st.button("Clear Credentials"):
                self.clear_session_state()
                st.rerun()
                
        else:
            st.error(f"An unexpected error occurred: {str(error)}")
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Retry"):
                    st.rerun()
            with col2:
                if st.button("Reset Session"):
                    self.clear_session_state()
                    st.rerun()

    def clear_session_state(self) -> None:
        """Clear session state safely"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    def retry_operation(self, operation: Callable, *args, **kwargs) -> Optional[Any]:
        """Retry an operation with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                wait_time = 2 ** attempt
                st.warning(f"Operation failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time) 