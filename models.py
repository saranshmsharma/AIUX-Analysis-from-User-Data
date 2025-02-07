from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class OptimizationType(enum.Enum):
    UX = "ux"
    PRICING = "pricing"
    INVENTORY = "inventory"
    MARKETING = "marketing"
    CHECKOUT = "checkout"

class ImplementationType(enum.Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    APPROVAL_NEEDED = "approval_needed"

class OptimizationStatus(enum.Enum):
    IDENTIFIED = "identified"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class ABTest(Base):
    __tablename__ = "ab_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String)  # active, completed, cancelled
    metrics = relationship("ABTestMetrics", back_populates="ab_test")
    created_at = Column(DateTime, default=datetime.utcnow)

class StoreAnalytics(Base):
    __tablename__ = "store_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    total_sales = Column(Float)
    total_orders = Column(Integer)
    average_order_value = Column(Float)
    conversion_rate = Column(Float)
    total_sessions = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON)

    def __init__(self, date, total_sales, total_orders, average_order_value, conversion_rate, total_sessions):
        self.date = date
        self.total_sales = total_sales
        self.total_orders = total_orders
        self.average_order_value = average_order_value
        self.conversion_rate = conversion_rate
        self.total_sessions = total_sessions

class ProductAnalytics(Base):
    __tablename__ = "product_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True)
    title = Column(String)
    total_sales = Column(Float)
    units_sold = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON)

class ShopifyCredentials(Base):
    __tablename__ = "shopify_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_url = Column(String, unique=True, index=True)
    access_token = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AIRecommendations(Base):
    __tablename__ = "ai_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shopify_credentials.id"))
    recommendation_type = Column(String)
    recommendation = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ABTestMetrics(Base):
    __tablename__ = "ab_test_metrics"
    id = Column(Integer, primary_key=True, index=True)
    ab_test_id = Column(Integer, ForeignKey("ab_tests.id"))
    variant = Column(String)  # A or B
    conversions = Column(Integer)
    visitors = Column(Integer)
    revenue = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    ab_test = relationship("ABTest", back_populates="metrics")

class StoreImprovementTip(Base):
    __tablename__ = "store_improvement_tips"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)
    title = Column(String)
    description = Column(String)
    impact = Column(String)
    effort = Column(String)
    implementation_steps = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, in_progress, completed

class StoreOptimization(Base):
    __tablename__ = "store_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    store_url = Column(String, index=True)
    optimization_type = Column(Enum(OptimizationType))
    implementation_type = Column(Enum(ImplementationType))
    status = Column(Enum(OptimizationStatus), default=OptimizationStatus.IDENTIFIED)
    
    title = Column(String)
    description = Column(String)
    revenue_impact = Column(Float)
    users_affected = Column(Integer)
    complexity_score = Column(Integer)  # 1-5
    risk_level = Column(Integer)  # 1-5
    
    implementation_steps = Column(JSON)
    rollback_steps = Column(JSON)
    
    before_metrics = Column(JSON)
    after_metrics = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    implemented_at = Column(DateTime, nullable=True)
    
    # Relationships
    revenue_tracking = relationship("OptimizationRevenue", back_populates="optimization")
    conversion_tracking = relationship("OptimizationConversion", back_populates="optimization")

class OptimizationRevenue(Base):
    __tablename__ = "optimization_revenue"

    id = Column(Integer, primary_key=True, index=True)
    optimization_id = Column(Integer, ForeignKey("store_optimizations.id"))
    date = Column(DateTime)
    revenue = Column(Float)
    predicted_revenue = Column(Float)
    actual_revenue = Column(Float)
    
    optimization = relationship("StoreOptimization", back_populates="revenue_tracking")

class OptimizationConversion(Base):
    __tablename__ = "optimization_conversion"

    id = Column(Integer, primary_key=True, index=True)
    optimization_id = Column(Integer, ForeignKey("store_optimizations.id"))
    date = Column(DateTime)
    funnel_step = Column(String)
    conversion_rate = Column(Float)
    users_affected = Column(Integer)
    
    optimization = relationship("StoreOptimization", back_populates="conversion_tracking") 