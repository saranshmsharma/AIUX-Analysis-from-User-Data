from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd
from models import StoreOptimization, OptimizationRevenue, OptimizationType
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class RevenuePredictionSystem:
    def __init__(self, db: Session):
        self.db = db
        self.scaler = StandardScaler()
        
    def predict_revenue_impact(
        self,
        optimization: StoreOptimization,
        historical_data: Dict[str, float],
        timeframe_days: int = 30
    ) -> Dict[str, float]:
        """
        Predict revenue impact of an optimization over specified timeframe
        """
        try:
            # Prepare historical data
            df = pd.DataFrame(historical_data)
            
            # Calculate baseline metrics
            baseline_daily_revenue = df['revenue'].mean()
            baseline_conversion_rate = df['conversion_rate'].mean()
            
            # Calculate impact multipliers based on optimization type
            impact_multiplier = self._calculate_impact_multiplier(
                optimization.optimization_type,
                optimization.complexity_score,
                optimization.users_affected
            )
            
            # Predict revenue increase
            predicted_increase = baseline_daily_revenue * impact_multiplier
            
            # Calculate confidence score based on historical data variance
            confidence_score = self._calculate_confidence_score(df, impact_multiplier)
            
            # Project revenue over timeframe
            daily_predictions = []
            cumulative_revenue = 0
            
            for day in range(timeframe_days):
                daily_revenue = baseline_daily_revenue * (1 + impact_multiplier)
                cumulative_revenue += daily_revenue
                daily_predictions.append({
                    'day': day + 1,
                    'predicted_revenue': daily_revenue,
                    'cumulative_revenue': cumulative_revenue
                })
            
            # Store prediction
            self._store_revenue_prediction(
                optimization.id,
                daily_predictions,
                confidence_score
            )
            
            return {
                'daily_baseline': baseline_daily_revenue,
                'predicted_daily_increase': predicted_increase,
                'predicted_total_increase': predicted_increase * timeframe_days,
                'confidence_score': confidence_score,
                'daily_predictions': daily_predictions
            }
            
        except Exception as e:
            logger.error(f"Error predicting revenue impact: {str(e)}")
            return None

    def _calculate_impact_multiplier(
        self,
        optimization_type: OptimizationType,
        complexity: int,
        users_affected: int
    ) -> float:
        """
        Calculate impact multiplier based on optimization characteristics
        """
        # Base multipliers for each optimization type
        type_multipliers = {
            OptimizationType.UX: 0.05,  # 5% baseline improvement
            OptimizationType.PRICING: 0.08,  # 8% baseline improvement
            OptimizationType.INVENTORY: 0.03,  # 3% baseline improvement
            OptimizationType.MARKETING: 0.10,  # 10% baseline improvement
            OptimizationType.CHECKOUT: 0.15   # 15% baseline improvement
        }
        
        # Get base multiplier for optimization type
        base_multiplier = type_multipliers.get(optimization_type, 0.05)
        
        # Adjust for complexity (higher complexity = lower expected impact)
        complexity_factor = 1 - ((complexity - 1) * 0.1)  # 10% reduction per complexity point
        
        # Adjust for users affected (more users = higher potential impact)
        user_factor = min(1 + (users_affected / 10000), 2.0)  # Cap at 2x multiplier
        
        return base_multiplier * complexity_factor * user_factor

    def _calculate_confidence_score(
        self,
        historical_data: pd.DataFrame,
        impact_multiplier: float
    ) -> float:
        """
        Calculate confidence score for prediction
        """
        # Calculate coefficient of variation
        cv = historical_data['revenue'].std() / historical_data['revenue'].mean()
        
        # Calculate data quality score
        data_quality = min(len(historical_data) / 30, 1.0)  # More data = higher confidence
        
        # Calculate impact size factor (larger impacts = lower confidence)
        impact_factor = 1 - (impact_multiplier / 2)
        
        # Combine factors into final confidence score
        confidence_score = (
            (1 - cv) * 0.4 +  # Data stability: 40%
            data_quality * 0.3 +  # Data quality: 30%
            impact_factor * 0.3   # Impact size: 30%
        )
        
        return max(min(confidence_score, 1.0), 0.0)  # Ensure score is between 0 and 1

    def _store_revenue_prediction(
        self,
        optimization_id: int,
        daily_predictions: List[Dict],
        confidence_score: float
    ) -> None:
        """
        Store revenue predictions in database
        """
        try:
            for prediction in daily_predictions:
                revenue_record = OptimizationRevenue(
                    optimization_id=optimization_id,
                    date=datetime.utcnow() + timedelta(days=prediction['day'] - 1),
                    predicted_revenue=prediction['predicted_revenue'],
                    actual_revenue=None  # To be updated later
                )
                self.db.add(revenue_record)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing revenue prediction: {str(e)}")
            self.db.rollback()

    def track_actual_revenue(
        self,
        optimization_id: int,
        actual_revenue: float,
        date: datetime
    ) -> None:
        """
        Track actual revenue for comparison with predictions
        """
        try:
            revenue_record = self.db.query(OptimizationRevenue).filter(
                OptimizationRevenue.optimization_id == optimization_id,
                OptimizationRevenue.date == date
            ).first()
            
            if revenue_record:
                revenue_record.actual_revenue = actual_revenue
                self.db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking actual revenue: {str(e)}")
            self.db.rollback()

    def get_revenue_comparison(
        self,
        optimization_id: int,
        days: int = 30
    ) -> Dict:
        """
        Get comparison of predicted vs actual revenue
        """
        try:
            revenue_data = self.db.query(OptimizationRevenue).filter(
                OptimizationRevenue.optimization_id == optimization_id,
                OptimizationRevenue.date >= datetime.utcnow() - timedelta(days=days)
            ).all()
            
            comparison = {
                'dates': [],
                'predicted': [],
                'actual': [],
                'variance': []
            }
            
            for record in revenue_data:
                comparison['dates'].append(record.date)
                comparison['predicted'].append(record.predicted_revenue)
                comparison['actual'].append(record.actual_revenue)
                
                if record.actual_revenue:
                    variance = ((record.actual_revenue - record.predicted_revenue) 
                              / record.predicted_revenue * 100)
                    comparison['variance'].append(variance)
                else:
                    comparison['variance'].append(None)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error getting revenue comparison: {str(e)}")
            return None 