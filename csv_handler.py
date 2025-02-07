
import pandas as pd
import streamlit as st

class CSVHandler:
    def __init__(self):
        self._orders_df = None
        self._products_df = None
        self._customers_df = None
    
    def import_orders(self, file):
        try:
            self._orders_df = pd.read_csv(file)
            return True
        except Exception as e:
            st.error(f"Error importing orders CSV: {str(e)}")
            return False
    
    def import_products(self, file):
        try:
            self._products_df = pd.read_csv(file)
            return True
        except Exception as e:
            st.error(f"Error importing products CSV: {str(e)}")
            return False
            
    def import_customers(self, file):
        try:
            self._customers_df = pd.read_csv(file)
            return True
        except Exception as e:
            st.error(f"Error importing customers CSV: {str(e)}")
            return False
    
    def get_orders_df(self):
        return self._orders_df
    
    def get_products_df(self):
        return self._products_df
    
    def get_customers_df(self):
        return self._customers_df
