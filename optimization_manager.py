from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from models import (
    StoreOptimization, 
    OptimizationType, 
    ImplementationType,
    OptimizationStatus,
    OptimizationRevenue,
    OptimizationConversion
)
from sqlalchemy.orm import Session
from openai import OpenAI

logger = logging.getLogger(__name__)

class OptimizationManager:
    def __init__(self, db: Session, openai_client: OpenAI):
        self.db = db
        self.openai_client = openai_client
        
    def analyze_conversion_funnel(self, store_url: str, analytics_data: Dict) -> List[Dict]:
        """Analyze conversion funnel and identify drop-off points"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert e-commerce analyst.
                    Analyze the conversion funnel data and identify specific drop-off points.
                    For each issue, provide:
                    1. Drop-off point description
                    2. Estimated revenue impact
                    3. Number of users affected
                    4. Possible optimization solution
                    5. Implementation complexity (1-5)
                    6. Risk level (1-5)"""},
                    {"role": "user", "content": f"Analyze this conversion funnel data and identify issues: {analytics_data}"}
                ],
                temperature=0.7
            )
            
            # Process the response and create optimization records
            issues = self._process_funnel_analysis(response.choices[0].message.content)
            
            for issue in issues:
                optimization = StoreOptimization(
                    store_url=store_url,
                    optimization_type=self._determine_optimization_type(issue),
                    implementation_type=self._determine_implementation_type(issue),
                    title=issue['title'],
                    description=issue['description'],
                    revenue_impact=issue['revenue_impact'],
                    users_affected=issue['users_affected'],
                    complexity_score=issue['complexity'],
                    risk_level=issue['risk'],
                    implementation_steps=issue['steps'],
                    rollback_steps=issue['rollback']
                )
                self.db.add(optimization)
            
            self.db.commit()
            return issues
            
        except Exception as e:
            logger.error(f"Error analyzing conversion funnel: {str(e)}")
            return []

    def _determine_optimization_type(self, issue: Dict) -> OptimizationType:
        """Determine the type of optimization based on the issue"""
        keywords = {
            OptimizationType.UX: ['layout', 'design', 'usability', 'navigation', 'mobile'],
            OptimizationType.PRICING: ['price', 'discount', 'offer', 'promotion'],
            OptimizationType.INVENTORY: ['stock', 'inventory', 'availability'],
            OptimizationType.MARKETING: ['advertising', 'campaign', 'promotion'],
            OptimizationType.CHECKOUT: ['cart', 'checkout', 'payment', 'shipping']
        }
        
        issue_text = f"{issue['title']} {issue['description']}".lower()
        
        for opt_type, words in keywords.items():
            if any(word in issue_text for word in words):
                return opt_type
                
        return OptimizationType.UX  # Default to UX if no clear match

    def _determine_implementation_type(self, issue: Dict) -> ImplementationType:
        """Determine the implementation type based on complexity and risk"""
        if issue['complexity'] <= 2 and issue['risk'] <= 2:
            return ImplementationType.AUTOMATIC
        elif issue['complexity'] >= 4 or issue['risk'] >= 4:
            return ImplementationType.MANUAL
        else:
            return ImplementationType.APPROVAL_NEEDED

    def get_pending_optimizations(self, store_url: str) -> List[StoreOptimization]:
        """Get list of pending optimizations for a store"""
        return self.db.query(StoreOptimization).filter(
            StoreOptimization.store_url == store_url,
            StoreOptimization.status.in_([
                OptimizationStatus.IDENTIFIED,
                OptimizationStatus.IN_PROGRESS
            ])
        ).all()

    def implement_optimization(self, optimization_id: int) -> bool:
        """Implement an optimization"""
        try:
            optimization = self.db.query(StoreOptimization).get(optimization_id)
            if not optimization:
                return False
                
            # Record before metrics
            optimization.before_metrics = self._get_current_metrics(optimization.store_url)
            
            # Implement based on type
            if optimization.implementation_type == ImplementationType.AUTOMATIC:
                success = self._implement_automatic(optimization)
            else:
                success = self._implement_manual(optimization)
                
            if success:
                optimization.status = OptimizationStatus.IMPLEMENTED
                optimization.implemented_at = datetime.utcnow()
                self.db.commit()
                
            return success
            
        except Exception as e:
            logger.error(f"Error implementing optimization: {str(e)}")
            return False 