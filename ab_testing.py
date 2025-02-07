from datetime import datetime
import json
from openai import OpenAI
import os
from database import get_db
from models import ABTest, ABTestMetrics, StoreImprovementTip

class ABTestingManager:
    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.db = next(get_db())
        
    def create_test(self, name: str, description: str):
        test = ABTest(
            name=name,
            description=description,
            status="active"
        )
        self.db.add(test)
        self.db.commit()
        return test
        
    def record_interaction(self, test_id, variant, interaction_type):
        """Record user interaction with a variant"""
        metric = ABTestMetrics.query.filter_by(
            test_id=test_id,
            variant=variant
        ).order_by(ABTestMetrics.timestamp.desc()).first()
        
        if not metric:
            metric = ABTestMetrics(test_id=test_id, variant=variant)
            
        if interaction_type == 'view':
            metric.views += 1
        elif interaction_type == 'click':
            metric.clicks += 1
        elif interaction_type == 'conversion':
            metric.conversions += 1
            
        self.db.add(metric)
        self.db.commit()
        
    def analyze_test_results(self, test_id):
        """Analyze A/B test results using AI"""
        test = ABTest.query.get(test_id)
        metrics_a = ABTestMetrics.query.filter_by(test_id=test_id, variant='A').all()
        metrics_b = ABTestMetrics.query.filter_by(test_id=test_id, variant='B').all()
        
        # Prepare test data for AI analysis
        test_data = {
            "test_name": test.name,
            "variant_a": {
                "config": test.variant_a,
                "metrics": {
                    "views": sum(m.views for m in metrics_a),
                    "clicks": sum(m.clicks for m in metrics_a),
                    "conversions": sum(m.conversions for m in metrics_a),
                    "revenue": sum(m.revenue for m in metrics_a)
                }
            },
            "variant_b": {
                "config": test.variant_b,
                "metrics": {
                    "views": sum(m.views for m in metrics_b),
                    "clicks": sum(m.clicks for m in metrics_b),
                    "conversions": sum(m.conversions for m in metrics_b),
                    "revenue": sum(m.revenue for m in metrics_b)
                }
            }
        }
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the A/B test results and provide insights. 
                        Format your response as JSON with the following structure:
                        {
                            "winner": "A" or "B" or null,
                            "confidence_score": float between 0 and 1,
                            "primary_insight": "string",
                            "detailed_analysis": [
                                {
                                    "metric": "string",
                                    "analysis": "string",
                                    "recommendation": "string"
                                }
                            ]
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these A/B test results: {json.dumps(test_data)}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Update test winner if confidence is high enough
            if analysis['confidence_score'] > 0.9:
                test.winner = analysis['winner']
                test.status = 'completed'
                self.db.commit()
                
            return analysis
            
        except Exception as e:
            return {
                "winner": None,
                "confidence_score": 0,
                "primary_insight": f"Error analyzing results: {str(e)}",
                "detailed_analysis": []
            }
            
    def generate_improvement_tip(self, store_url, analytics_data):
        """Generate AI-powered store improvement tips"""
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {
                        "role": "system",
                        "content": """Generate a store improvement tip based on the analytics data.
                        Format your response as JSON with the following structure:
                        {
                            "tip_type": "ux|inventory|pricing|marketing",
                            "title": "string",
                            "content": "string",
                            "priority": integer 1-5,
                            "expected_impact": "string"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"Generate improvement tip based on: {json.dumps(analytics_data)}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            tip_data = json.loads(response.choices[0].message.content)
            
            tip = StoreImprovementTip(
                store_url=store_url,
                tip_type=tip_data['tip_type'],
                title=tip_data['title'],
                content=tip_data['content'],
                priority=tip_data['priority']
            )
            
            self.db.add(tip)
            self.db.commit()
            
            return tip_data
            
        except Exception as e:
            return {
                "tip_type": "error",
                "title": "Error Generating Tip",
                "content": str(e),
                "priority": 1,
                "expected_impact": "none"
            }
