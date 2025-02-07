import sys
import os
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from src.data_processor import DataProcessor
from src.learning_system import LearningSystem
from src.ml_engine import MLEngine
from src.openai_manager import OpenAIManager
from src.shopify_integration import ShopifyIntegration
from src.visualization import Visualization

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add PredictAI to Python path
current_dir = Path(__file__).parent
predictai_dir = current_dir / 'PredictAI'
src_dir = predictai_dir / 'src'
sys.path.append(str(predictai_dir))
sys.path.append(str(src_dir))

try:
    # Direct imports from src directory
    from src.data_processor import DataProcessor
    from src.learning_system import LearningSystem
    from src.ml_engine import MLEngine
    from src.openai_manager import OpenAIManager
    from src.shopify_integration import ShopifyIntegration
    from src.visualization import Visualization
    
    logger.info("Successfully imported PredictAI modules")
except ImportError as e:
    logger.error(f"Failed to import PredictAI modules: {str(e)}")
    logger.error(f"Current PYTHONPATH: {sys.path}")
    logger.error(f"Looking for modules in: {src_dir}")
    raise ImportError("Failed to import required PredictAI modules") from e

# Load environment variables
load_dotenv()

class PredictAIIntegration:
    """Integration class to connect PredictAI with ShopAI Insight."""
    
    def __init__(self, shopify_token=None):
        try:
            self.shopify_token = shopify_token
            
            # Initialize all PredictAI components
            self.shopify_integration = ShopifyIntegration(shopify_token)
            self.data_processor = DataProcessor()
            self.ml_engine = MLEngine()
            self.learning_system = LearningSystem()
            self.openai_manager = OpenAIManager()
            self.visualization = Visualization()
            
            # Initialize learning system
            self.learning_system.initialize_db()
            
            logger.info("PredictAI integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PredictAI integration: {str(e)}")
            logger.error(f"Current directory: {os.getcwd()}")
            logger.error(f"PredictAI directory exists: {predictai_dir.exists()}")
            logger.error(f"src directory exists: {src_dir.exists()}")
            raise
    
    def process_data(self, data):
        """Process input data through the PredictAI pipeline."""
        try:
            # Convert data to PredictAI format
            processed_data = self.data_processor.process(data)
            
            # Extract features
            features = self.data_processor.extract_features(processed_data)
            
            # Validate data
            if self.data_processor.validate_data(features):
                return features
            else:
                logger.error("Data validation failed")
                return None
        except Exception as e:
            logger.error(f"Data processing error: {str(e)}")
            return None
    
    def get_predictions(self, data):
        """Get predictions using PredictAI models."""
        try:
            # Process data
            processed_data = self.process_data(data)
            if processed_data is None:
                return None
            
            # Generate ML predictions
            ml_predictions = self.ml_engine.predict(processed_data)
            
            # Get OpenAI insights
            ai_insights = self.openai_manager.generate_insights(ml_predictions)
            
            # Prepare visualization data
            viz_data = self.visualization.prepare_data(ml_predictions)
            
            # Store predictions for learning
            self.learning_system.store_prediction(
                prediction_data=ml_predictions,
                timestamp=datetime.now()
            )
            
            return {
                'predictions': ml_predictions,
                'insights': ai_insights,
                'visualization_data': viz_data
            }
        except Exception as e:
            logger.error(f"PredictAI prediction error: {str(e)}")
            return None

    def get_learning_insights(self, historical_data):
        """Get learning insights from historical data."""
        try:
            # Process historical data
            processed_historical = self.process_data(historical_data)
            if processed_historical is None:
                return None
            
            # Get learning insights
            learning_metrics = self.learning_system.analyze(processed_historical)
            
            # Get performance trends
            performance_trends = self.learning_system.get_performance_trends()
            
            return {
                'metrics': learning_metrics,
                'trends': performance_trends,
                'recommendations': self.generate_recommendations(learning_metrics)
            }
        except Exception as e:
            logger.error(f"Learning system error: {str(e)}")
            return None
            
    def generate_recommendations(self, metrics):
        """Generate recommendations based on learning metrics."""
        try:
            return self.openai_manager.generate_recommendations(metrics)
        except Exception as e:
            logger.error(f"Recommendation generation error: {str(e)}")
            return []

class Integration:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.learning_system = LearningSystem()
        self.ml_engine = MLEngine()
        self.openai_manager = OpenAIManager()
        self.shopify_integration = ShopifyIntegration()
        self.visualization = Visualization()

    def process_and_analyze(self):
        """Main processing and analysis pipeline."""
        try:
            # Fetch data from Shopify
            raw_data = self.shopify_integration.fetch_data()
            if raw_data is None:
                return None

            # Process the data
            processed_data = self.data_processor.process_data(raw_data)
            if processed_data is None:
                return None

            # Train the learning system
            self.learning_system.train(processed_data)

            # Make predictions
            predictions = self.ml_engine.predict(processed_data)

            # Create visualizations
            visualizations = self.visualization.create_sales_chart(processed_data)

            return {
                'processed_data': processed_data,
                'predictions': predictions,
                'visualizations': visualizations
            }

        except Exception as e:
            print(f"Error in integration pipeline: {e}")
            return None

    def get_ai_insights(self, query):
        """Get AI-powered insights using OpenAI."""
        try:
            return self.openai_manager.get_response(query)
        except Exception as e:
            print(f"Error getting AI insights: {e}")
            return None 