from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
from prophet import Prophet
import logging

logger = logging.getLogger(__name__)

class AdvancedPredictionSystem:
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100),
            'gradient_boost': GradientBoostingRegressor(),
            'xgboost': xgb.XGBRegressor(),
            'prophet': Prophet()
        }
        self.scaler = StandardScaler()

    def predict_with_ensemble(
        self,
        historical_data: pd.DataFrame,
        features: List[str],
        target: str,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Make predictions using an ensemble of models
        """
        try:
            predictions = {}
            confidence_scores = {}
            
            # Prepare data
            X = historical_data[features]
            y = historical_data[target]
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
            
            # Train and predict with each model
            for model_name, model in self.models.items():
                if model_name == 'prophet':
                    # Special handling for Prophet
                    prophet_df = pd.DataFrame({
                        'ds': historical_data.index,
                        'y': historical_data[target]
                    })
                    model.fit(prophet_df)
                    future_dates = model.make_future_dataframe(periods=forecast_days)
                    forecast = model.predict(future_dates)
                    predictions[model_name] = forecast['yhat'].tail(forecast_days).values
                else:
                    # Traditional ML models
                    model.fit(X_train, y_train)
                    predictions[model_name] = model.predict(X_test)
                    confidence_scores[model_name] = model.score(X_test, y_test)
            
            # Ensemble predictions with weighted average
            weights = self._calculate_model_weights(confidence_scores)
            ensemble_prediction = np.zeros(forecast_days)
            
            for model_name, preds in predictions.items():
                if model_name in weights:
                    ensemble_prediction += preds * weights[model_name]
            
            return {
                'ensemble_prediction': ensemble_prediction,
                'individual_predictions': predictions,
                'confidence_scores': confidence_scores,
                'model_weights': weights
            }
            
        except Exception as e:
            logger.error(f"Error in ensemble prediction: {str(e)}")
            return None

    def _calculate_model_weights(
        self,
        confidence_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate weights for each model based on performance"""
        total_score = sum(confidence_scores.values())
        if total_score == 0:
            # Equal weights if all scores are 0
            return {model: 1.0/len(confidence_scores) for model in confidence_scores}
        return {
            model: score/total_score 
            for model, score in confidence_scores.items()
        }

    def calculate_prediction_intervals(
        self,
        predictions: np.ndarray,
        confidence_level: float = 0.95
    ) -> Dict[str, np.ndarray]:
        """Calculate prediction intervals"""
        std_dev = np.std(predictions)
        z_score = 1.96  # 95% confidence interval
        
        return {
            'lower_bound': predictions - (z_score * std_dev),
            'upper_bound': predictions + (z_score * std_dev)
        }

    def get_forecast_metrics(
        self,
        predictions: np.ndarray,
        historical_data: np.ndarray
    ) -> Dict[str, Any]:
        """Calculate forecast metrics"""
        return {
            'growth_rate': ((predictions.mean() - historical_data.mean()) 
                           / historical_data.mean() * 100),
            'confidence_score': 95.0,  # Placeholder for now
            'forecast_days': len(predictions)
        } 