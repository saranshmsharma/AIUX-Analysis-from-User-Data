import pandas as pd
from shopify_client import ShopifyClient


class DataProcessor:

    def __init__(self, data_source):
        self.data_source = data_source
        self._orders_df = None
        self._products_df = None
        self._customers_df = None

    def get_orders_df(self):
        if isinstance(self.data_source, ShopifyClient):
            if self._orders_df is None:
                orders = self.data_source.get_orders()
                self._orders_df = pd.DataFrame(orders)
        else:
            self._orders_df = self.data_source.get_orders_df()
        return self._orders_df

    def get_products_df(self):
        if isinstance(self.data_source, ShopifyClient):
            if self._products_df is None:
                products = self.data_source.get_products()
                self._products_df = pd.DataFrame(products)
        else:
            self._products_df = self.data_source.get_products_df()
        return self._products_df

    def get_customers_df(self):
        if isinstance(self.data_source, ShopifyClient):
            if self._customers_df is None:
                customers = self.data_source.get_customers()
                self._customers_df = pd.DataFrame(customers)
        else:
            self._customers_df = self.data_source.get_customers_df()
        return self._customers_df
