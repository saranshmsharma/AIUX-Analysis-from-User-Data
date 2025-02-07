import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import pandas as pd
from typing import Dict, List

class AdvancedVisualization:
    @staticmethod
    def render_revenue_forecast(
        predictions: Dict,
        historical_data: pd.DataFrame,
        date_column: str,
        actual_column: str
    ):
        """Render advanced revenue forecast visualization"""
        
        # Create main figure with secondary y-axis
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Revenue Forecast',
                'Model Performance Comparison',
                'Prediction Intervals',
                'Model Confidence Scores'
            ),
            specs=[[{"secondary_y": True}, {}],
                  [{}, {"type": "domain"}]]
        )
        
        # Plot 1: Revenue Forecast
        fig.add_trace(
            go.Scatter(
                x=historical_data[date_column],
                y=historical_data[actual_column],
                name="Historical Revenue",
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=pd.date_range(
                    start=historical_data[date_column].max(),
                    periods=len(predictions['ensemble_prediction']),
                    freq='D'
                ),
                y=predictions['ensemble_prediction'],
                name="Ensemble Forecast",
                line=dict(color='red', dash='dash')
            ),
            row=1, col=1
        )
        
        # Plot 2: Model Performance Comparison
        for model_name, preds in predictions['individual_predictions'].items():
            fig.add_trace(
                go.Scatter(
                    y=preds,
                    name=f"{model_name} Predictions",
                    mode='lines',
                    opacity=0.7
                ),
                row=1, col=2
            )
        
        # Plot 3: Prediction Intervals
        intervals = predictions.get('prediction_intervals', {})
        if intervals:
            fig.add_trace(
                go.Scatter(
                    y=intervals['upper_bound'],
                    y0=intervals['lower_bound'],
                    name="Prediction Interval",
                    fill='tonexty',
                    mode='lines',
                    line=dict(width=0),
                    fillcolor='rgba(231,234,241,0.5)'
                ),
                row=2, col=1
            )
        
        # Plot 4: Model Confidence Scores
        fig.add_trace(
            go.Pie(
                labels=list(predictions['confidence_scores'].keys()),
                values=list(predictions['confidence_scores'].values()),
                name="Model Confidence"
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Advanced Revenue Forecast Analysis",
            hovermode='x unified'
        )
        
        return fig

    @staticmethod
    def render_optimization_impact(
        optimization_data: Dict,
        historical_metrics: pd.DataFrame
    ):
        """Render optimization impact visualization"""
        
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Revenue Impact',
                'Conversion Rate Change',
                'User Engagement Metrics',
                'ROI Analysis'
            ),
            specs=[[{"secondary_y": True}, {"secondary_y": True}],
                  [{"secondary_y": True}, {"secondary_y": True}]]
        )
        
        # Add traces for each subplot
        # Revenue Impact
        fig.add_trace(
            go.Scatter(
                x=historical_metrics.index,
                y=historical_metrics['revenue'],
                name="Actual Revenue",
                line=dict(color='blue')
            ),
            row=1, col=1, secondary_y=False
        )
        
        # Conversion Rate
        fig.add_trace(
            go.Scatter(
                x=historical_metrics.index,
                y=historical_metrics['conversion_rate'],
                name="Conversion Rate",
                line=dict(color='green')
            ),
            row=1, col=2, secondary_y=False
        )
        
        # User Engagement
        fig.add_trace(
            go.Bar(
                x=historical_metrics.index,
                y=historical_metrics['user_engagement'],
                name="User Engagement"
            ),
            row=2, col=1, secondary_y=False
        )
        
        # ROI Analysis
        fig.add_trace(
            go.Scatter(
                x=historical_metrics.index,
                y=historical_metrics['roi'],
                name="ROI",
                line=dict(color='purple')
            ),
            row=2, col=2, secondary_y=False
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Optimization Impact Analysis",
            hovermode='x unified'
        )
        
        return fig

    @staticmethod
    def render_metrics_dashboard(metrics: Dict):
        """Render metrics dashboard"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Revenue Impact",
                f"${metrics['revenue_impact']:,.2f}",
                f"{metrics['revenue_change']:+.1f}%",
                delta_color="normal"
            )
            
        with col2:
            st.metric(
                "Conversion Rate",
                f"{metrics['conversion_rate']:.2f}%",
                f"{metrics['conversion_change']:+.1f}%",
                delta_color="normal"
            )
            
        with col3:
            st.metric(
                "ROI",
                f"{metrics['roi']:.1f}x",
                f"{metrics['roi_change']:+.1f}x",
                delta_color="normal"
            )
        
        # Add detailed metrics expansion
        with st.expander("View Detailed Metrics"):
            st.write("### Detailed Performance Metrics")
            st.dataframe(pd.DataFrame(metrics['detailed_metrics'])) 