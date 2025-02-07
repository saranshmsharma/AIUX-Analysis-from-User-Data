from sqlalchemy.orm import Session
import models

def create_shop_credentials(db: Session, shop_url: str, access_token: str):
    db_credentials = models.ShopifyCredentials(
        shop_url=shop_url,
        access_token=access_token
    )
    db.add(db_credentials)
    db.commit()
    db.refresh(db_credentials)
    return db_credentials

def get_shop_credentials(db: Session, shop_url: str):
    return db.query(models.ShopifyCredentials).filter(
        models.ShopifyCredentials.shop_url == shop_url
    ).first()

def create_store_analytics(db: Session, shop_id: int, total_sales: float, 
                         total_orders: int, average_order_value: float):
    db_analytics = models.StoreAnalytics(
        shop_id=shop_id,
        total_sales=total_sales,
        total_orders=total_orders,
        average_order_value=average_order_value
    )
    db.add(db_analytics)
    db.commit()
    db.refresh(db_analytics)
    return db_analytics

def create_ab_test(db: Session, name: str, description: str):
    db_test = models.ABTest(
        name=name,
        description=description,
        status="active"
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

def get_store_analytics(db: Session, shop_id: int):
    return db.query(models.StoreAnalytics).filter(
        models.StoreAnalytics.shop_id == shop_id
    ).all() 