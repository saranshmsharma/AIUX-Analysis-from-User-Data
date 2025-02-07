import streamlit as st

class AuthHandler:
    def __init__(self):
        """Initialize AuthHandler without authentication."""
        pass

    def login(self):
        """Bypass login process."""
        st.session_state.user_info = {"name": "Guest", "email": "guest@example.com"}
        return True

    def logout(self):
        """No logout process needed."""
        pass

    def is_authenticated(self):
        """Always return True for guest access."""
        return True

    def get_user_info(self):
        """Return guest user info."""
        return st.session_state.user_info 