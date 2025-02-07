from openai import OpenAI
import os
from typing import Dict, List
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('AIRecommender')

class AIRecommender:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=self.api_key)
        logger.info("AIRecommender initialized")

    def get_improvement_tips(self, analytics_data: Dict) -> List[Dict]:
        """Generate AI-powered improvement tips based on analytics data"""
        try:
            if not analytics_data:
                logger.warning("No analytics data provided")
                return []

            # Prepare the context for GPT
            context = self._prepare_analytics_context(analytics_data)
            logger.debug(f"Prepared context: {context}")
            
            # Generate recommendations using GPT-4
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": """You are an expert e-commerce analyst. 
                        Provide exactly 3 specific, actionable recommendations to improve the store's performance.
                        Format each recommendation with Action:, Impact:, Implementation:, and Goal: sections."""},
                        {"role": "user", "content": f"""
                        Based on this store data, provide 3 specific recommendations:
                        {context}
                        
                        Format each recommendation as:
                        Action: (what to do)
                        Impact: (expected benefit)
                        Implementation: (specific steps)
                        Goal: (measurable target)
                        """}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                logger.info("Successfully generated recommendations")
                recommendations = self._process_gpt_response(response.choices[0].message.content)
                logger.debug(f"Processed recommendations: {recommendations}")
                return recommendations

            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                return [{"action": f"API Error: {str(e)}", "impact": "Please try again", "implementation": "", "goal": ""}]

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return [{"action": "Error", "impact": str(e), "implementation": "", "goal": ""}]

    def _prepare_analytics_context(self, analytics_data: Dict) -> str:
        """Prepare analytics data as context for GPT"""
        try:
            context = f"""
            Store Performance:
            - Total Sales: ${analytics_data.get('total_sales', 0):,.2f}
            - Total Orders: {analytics_data.get('total_orders', 0)}
            - Average Order Value: ${analytics_data.get('average_order_value', 0):,.2f}
            - Conversion Rate: {analytics_data.get('conversion_rate', 0)}%
            """
            
            # Add top products if available
            if 'top_products' in analytics_data and analytics_data['top_products']:
                context += "\nTop Products:\n"
                context += self._format_top_products(analytics_data['top_products'])
            
            # Add sales trends if available
            if 'sales_trends' in analytics_data and analytics_data['sales_trends']:
                context += "\nSales Trends:\n"
                context += self._format_sales_trends(analytics_data['sales_trends'])
            
            return context

        except Exception as e:
            logger.error(f"Error preparing context: {str(e)}")
            return "Error preparing analytics context"

    def _format_top_products(self, products: List[Dict]) -> str:
        try:
            return "\n".join([
                f"- {product.get('title', 'Unknown')}: ${float(product.get('price', 0)):,.2f}"
                for product in products
            ])
        except Exception as e:
            logger.error(f"Error formatting products: {str(e)}")
            return "Error formatting products"

    def _format_sales_trends(self, trends: Dict) -> str:
        try:
            if not trends or 'daily_sales' not in trends:
                return "No sales trend data available"
            
            daily_sales = trends['daily_sales']
            if len(daily_sales) > 1:
                latest = float(daily_sales[-1].get('daily_sales', 0))
                previous = float(daily_sales[-2].get('daily_sales', 0))
                trend = "increasing" if latest > previous else "decreasing"
                return f"Sales are {trend}. Latest daily sales: ${latest:,.2f}"
            return "Insufficient data for trend analysis"
            
        except Exception as e:
            logger.error(f"Error formatting sales trends: {str(e)}")
            return "Error formatting sales trends"

    def _process_gpt_response(self, response: str) -> List[Dict]:
        """Process GPT response into structured recommendations"""
        try:
            recommendations = []
            current_rec = {}
            
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('Action:'):
                    if current_rec:
                        recommendations.append(current_rec)
                    current_rec = {'action': line[7:].strip()}
                elif line.startswith('Impact:'):
                    current_rec['impact'] = line[7:].strip()
                elif line.startswith('Implementation:'):
                    current_rec['implementation'] = line[15:].strip()
                elif line.startswith('Goal:'):
                    current_rec['goal'] = line[5:].strip()
            
            if current_rec:
                recommendations.append(current_rec)
            
            return recommendations if recommendations else [
                {
                    "action": "No recommendations generated",
                    "impact": "Please try again",
                    "implementation": "",
                    "goal": ""
                }
            ]
            
        except Exception as e:
            logger.error(f"Error processing GPT response: {str(e)}")
            return [
                {
                    "action": "Error processing recommendations",
                    "impact": str(e),
                    "implementation": "",
                    "goal": ""
                }
            ]

    def get_custom_insights(self, analytics_data: Dict, goal: str) -> List[Dict]:
        """Generate custom insights based on specific business goals"""
        try:
            context = self._prepare_analytics_context(analytics_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert e-commerce strategist.
                    Analyze the store data and provide specific insights and recommendations
                    to help achieve the specified business goal. Format your response clearly with numbered insights."""},
                    {"role": "user", "content": f"""
                    Goal: {goal}
                    
                    Store Analytics:
                    {context}
                    
                    Provide 3 specific insights and recommendations to achieve this goal.
                    Format each insight exactly as follows:
                    
                    Insight 1:
                    Current Status: (describe current situation)
                    Gap Analysis: (identify gaps)
                    Specific Actions: (list actions)
                    Success Metrics: (define metrics)
                    
                    (repeat for insights 2 and 3)
                    """}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            insights = self._process_goal_insights(response.choices[0].message.content)
            logger.debug(f"Processed insights: {insights}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating goal-based insights: {str(e)}")
            return [{
                "insight": "Error generating insights",
                "current_status": str(e),
                "gap_analysis": "Please try again",
                "specific_actions": "Contact support if error persists",
                "success_metrics": "N/A"
            }]

    def _process_goal_insights(self, response: str) -> List[Dict]:
        """Process goal-based insights into structured format"""
        try:
            insights = []
            current_insight = {}
            insight_number = 1
            
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('Insight'):
                    if current_insight and len(current_insight) >= 4:  # Make sure we have all required fields
                        insights.append(current_insight)
                    current_insight = {
                        "insight": f"Insight {insight_number}"
                    }
                    insight_number += 1
                elif line.startswith('Current Status:'):
                    current_insight['current_status'] = line[14:].strip()
                elif line.startswith('Gap Analysis:'):
                    current_insight['gap_analysis'] = line[12:].strip()
                elif line.startswith('Specific Actions:'):
                    current_insight['specific_actions'] = line[16:].strip()
                elif line.startswith('Success Metrics:'):
                    current_insight['success_metrics'] = line[15:].strip()
            
            # Add the last insight if it's complete
            if current_insight and len(current_insight) >= 4:
                insights.append(current_insight)
            
            # If no insights were processed, return a default message
            if not insights:
                return [{
                    "insight": "Insight 1",
                    "current_status": "No insights generated",
                    "gap_analysis": "Please try again",
                    "specific_actions": "Contact support if error persists",
                    "success_metrics": "N/A"
                }]
            
            return insights
            
        except Exception as e:
            logger.error(f"Error processing goal insights: {str(e)}")
            return [{
                "insight": "Error processing insights",
                "current_status": str(e),
                "gap_analysis": "Please try again",
                "specific_actions": "Contact support if error persists",
                "success_metrics": "N/A"
            }]

    def _ensure_complete_insight(self, insight: Dict) -> Dict:
        """Ensure all required fields are present in an insight"""
        required_fields = ['current_status', 'gap_analysis', 'specific_actions', 'success_metrics']
        for field in required_fields:
            if field not in insight:
                insight[field] = "Not provided"
        return insight
