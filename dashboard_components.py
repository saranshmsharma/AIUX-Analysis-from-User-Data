import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import logging
from functools import lru_cache

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_custom_css():
    st.markdown("""
        <style>
        /* Card styling */
        .metric-card {
            background-color: #ffffff;
            border-radius: 0.8rem;
            padding: 1.5rem;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Section styling */
        .section-header {
            padding: 1rem;
            margin: 1.5rem 0 1rem 0;
            border-bottom: 2px solid #f0f2f6;
            font-size: 1.5rem;
            font-weight: 600;
            color: #1a1a1a;
        }
        
        /* Insight card styling */
        .insight-card {
            background-color: #ffffff;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #2E86C1;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Recommendation card styling */
        .recommendation-card {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid #e0e0e0;
        }
        
        /* Chart container styling */
        .chart-container {
            background-color: #ffffff;
            border-radius: 0.8rem;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Table styling */
        .dataframe {
            border-radius: 0.5rem !important;
            overflow: hidden;
            border: 1px solid #e0e0e0 !important;
        }
        
        /* Animation for cards */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-fade-in {
            animation: fadeIn 0.5s ease-out forwards;
        }
        </style>
    """, unsafe_allow_html=True)

# Cache store data processing
@st.cache_data(ttl=3600)  # Cache for 1 hour
def process_store_data(store_data):
    """Process and cache store data for visualizations"""
    return {
        'total_sales': store_data['total_sales'],
        'total_orders': store_data['total_orders'],
        'avg_order_value': store_data['avg_order_value'],
        'active_customers': store_data['active_customers'],
        'sales_by_category': pd.DataFrame(store_data['sales_by_category']),
        'daily_sales': pd.DataFrame({
            'dates': store_data['dates'],
            'sales': store_data['daily_sales']
        }),
        'customer_insights': store_data.get('customer_insights', []),
        'recommendations': store_data.get('recommendations', {}),
        'top_products': pd.DataFrame(store_data['top_products']),
        'sales_by_channel': pd.DataFrame(store_data['sales_by_channel'])
    }

# Cache individual visualizations
@st.cache_data(ttl=3600)
def create_sales_trend_chart(dates, daily_sales):
    """Create and cache sales trend visualization"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=daily_sales,
        mode='lines+markers',
        name='Daily Sales',
        line=dict(color='#2E86C1'),
        marker=dict(size=6)
    ))
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Date",
        yaxis_title="Sales ($)",
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        )
    )
    return fig

@st.cache_data(ttl=3600)
def create_category_chart(sales_by_category):
    """Create and cache category sales visualization"""
    fig = px.pie(
        sales_by_category,
        values='sales',
        names='category',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig

def render_header():
    """Render the dashboard header"""
    st.title("Shop AI Insight Dashboard")
    st.markdown("---")

def render_metrics(analytics_data):
    """Render key metrics in columns"""
    if not analytics_data:
        st.error("No analytics data available")
        return

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", f"${analytics_data['total_sales']:,.2f}")
    with col2:
        st.metric("Total Orders", analytics_data['total_orders'])
    with col3:
        st.metric("Avg Order Value", f"${analytics_data['average_order_value']:,.2f}")
    with col4:
        st.metric("Conversion Rate", f"{analytics_data['conversion_rate']:.1f}%")

def render_visualizations(sales_data):
    """Render data visualizations"""
    st.subheader("Sales Trends")
    
    if not sales_data:
        st.warning("No sales data available")
        return

    try:
        # Daily sales chart
        if 'daily_sales' in sales_data:
            daily_df = pd.DataFrame(sales_data['daily_sales'])
            fig_daily = px.line(
                daily_df, 
                x='date', 
                y='daily_sales',
                title='Daily Sales Trend'
            )
            st.plotly_chart(fig_daily)

        # Weekly sales chart
        if 'weekly_sales' in sales_data:
            weekly_df = pd.DataFrame(sales_data['weekly_sales'])
            fig_weekly = px.line(
                weekly_df, 
                x='date', 
                y='weekly_sales',
                title='Weekly Sales Trend'
            )
            st.plotly_chart(fig_weekly)

    except Exception as e:
        st.error(f"Error rendering visualizations: {str(e)}")

def render_recommendations(recommendations):
    """Render AI recommendations"""
    st.subheader("AI Insights & Recommendations")
    
    if not recommendations:
        st.warning("No recommendations available")
        return

    for i, rec in enumerate(recommendations, 1):
        with st.expander(f"Recommendation {i}: {rec.get('action', 'No action specified')}", expanded=i==1):
            st.write("**Impact:**", rec.get('impact', 'Not specified'))
            st.write("**Implementation:**", rec.get('implementation', 'Not specified'))
            st.write("**Goal:**", rec.get('goal', 'Not specified'))
            
            # Add action buttons with unique keys
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Mark as Done", key=f"done_rec_{i}"):
                    st.success("Marked as completed!")
            with col2:
                if st.button("Set Reminder", key=f"reminder_rec_{i}"):
                    st.info("Reminder set!")

def render_ab_test_results():
    """Render A/B test results"""
    st.subheader("A/B Test Results")
    # Add A/B test results rendering logic here
    st.info("A/B Testing feature coming soon!")

def render_goal_insights(insights):
    st.subheader("Goal-Specific Insights")
    
    if not insights:
        st.warning("No goal-specific insights available")
        return

    for i, insight in enumerate(insights, 1):
        with st.expander(f"📊 Insight {i}", expanded=i==1):
            st.markdown(f"**{insight.get('insight', f'Insight {i}')}**")
            st.write("**Current Status:**", insight.get('current_status', 'Not specified'))
            st.write("**Gap Analysis:**", insight.get('gap_analysis', 'Not specified'))
            st.write("**Specific Actions:**", insight.get('specific_actions', 'Not specified'))
            st.write("**Success Metrics:**", insight.get('success_metrics', 'Not specified'))
            
            # Add progress tracking with unique key
            progress = st.slider(
                "Implementation Progress", 
                0, 100, 0, 
                key=f"progress_insight_{i}"
            )
            st.progress(progress / 100.0)
            
            # Action buttons with unique keys
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Mark Complete", key=f"done_insight_{i}"):
                    st.success("Marked as completed!")
            with col2:
                if st.button("Set Reminder", key=f"reminder_insight_{i}"):
                    st.info("Reminder set!")

def generate_detailed_recommendations(data):
    """Generate detailed store recommendations."""
    recommendations = []
    try:
        metrics = data.get('metrics', {})
        sales_df = data.get('sales', pd.DataFrame())
        
        # Revenue Recommendations
        total_sales = metrics.get('total_sales', 0)
        revenue_change = metrics.get('revenue_change_percentage', 0)
        recommendations.append({
            'priority': 'Critical' if revenue_change < 0 else 'High',
            'category': 'Revenue',
            'title': 'Revenue Optimization',
            'current_state': f'Current total sales: ${total_sales:,.2f}',
            'target_state': f'Target: Increase revenue by 20%',
            'gap': f'Revenue change: {revenue_change:+.1f}%',
            'action_items': [
                'Implement dynamic pricing strategy',
                'Launch targeted promotional campaigns',
                'Optimize product mix',
                'Increase average order value through bundles'
            ],
            'expected_impact': 'Increase revenue by 20% in 3 months',
            'implementation_time': 'Short-term'
        })

        # Customer Experience Recommendations
        conv_rate = metrics.get('conversion_rate', 0)
        recommendations.append({
            'priority': 'High',
            'category': 'Customer Experience',
            'title': 'Conversion Rate Optimization',
            'current_state': f'Current conversion rate: {conv_rate:.2f}%',
            'target_state': 'Target conversion rate: 3.00%',
            'gap': f'{(3 - conv_rate):.2f}% below target',
            'action_items': [
                'Optimize website navigation',
                'Improve product page layouts',
                'Streamline checkout process',
                'Add customer reviews and social proof'
            ],
            'expected_impact': 'Increase conversion rate by 1% in 60 days',
            'implementation_time': 'Medium-term'
        })

        # Marketing Recommendations
        marketing_spend = metrics.get('marketing_spend', 0)
        roas = total_sales / marketing_spend if marketing_spend > 0 else 0
        recommendations.append({
            'priority': 'High',
            'category': 'Marketing',
            'title': 'Marketing Efficiency',
            'current_state': f'Current ROAS: {roas:.2f}x',
            'target_state': 'Target ROAS: 4.0x',
            'gap': f'{(4 - roas):.2f}x below target',
            'action_items': [
                'Optimize ad spend allocation',
                'Improve targeting parameters',
                'Implement retargeting campaigns',
                'Focus on high-performing channels'
            ],
            'expected_impact': 'Improve ROAS by 25% in 45 days',
            'implementation_time': 'Medium-term'
        })

        # Operations Recommendations
        recommendations.append({
            'priority': 'Medium',
            'category': 'Operations',
            'title': 'Operational Efficiency',
            'current_state': 'Current: Manual processes',
            'target_state': 'Target: Automated workflows',
            'gap': 'Need for automation and optimization',
            'action_items': [
                'Automate order processing',
                'Implement inventory management system',
                'Streamline fulfillment process',
                'Set up automated customer service responses'
            ],
            'expected_impact': 'Reduce operational costs by 15%',
            'implementation_time': 'Long-term'
        })

        # Customer Retention Recommendations
        returning_customers = metrics.get('returning_customers', 0)
        total_customers = metrics.get('total_customers', 1)
        retention_rate = (returning_customers / total_customers * 100) if total_customers > 0 else 0
        recommendations.append({
            'priority': 'High',
            'category': 'Customer Retention',
            'title': 'Customer Loyalty Program',
            'current_state': f'Current retention rate: {retention_rate:.1f}%',
            'target_state': 'Target retention rate: 40%',
            'gap': f'{(40 - retention_rate):.1f}% below target',
            'action_items': [
                'Launch loyalty rewards program',
                'Implement post-purchase follow-up',
                'Create VIP customer segments',
                'Develop customer feedback program'
            ],
            'expected_impact': 'Increase customer retention by 15%',
            'implementation_time': 'Medium-term'
        })

        # Website Performance Recommendations
        recommendations.append({
            'priority': 'Medium',
            'category': 'Website Performance',
            'title': 'Site Speed Optimization',
            'current_state': 'Current: Variable performance',
            'target_state': 'Target: Optimal speed and reliability',
            'gap': 'Performance optimization needed',
            'action_items': [
                'Optimize image sizes',
                'Implement caching',
                'Minimize HTTP requests',
                'Upgrade hosting if needed'
            ],
            'expected_impact': 'Improve page load times by 40%',
            'implementation_time': 'Short-term'
        })

        # Product Strategy Recommendations
        recommendations.append({
            'priority': 'High',
            'category': 'Product Strategy',
            'title': 'Product Mix Optimization',
            'current_state': 'Current: Basic product offering',
            'target_state': 'Target: Optimized product mix',
            'gap': 'Product range expansion needed',
            'action_items': [
                'Analyze product performance metrics',
                'Identify top-selling categories',
                'Expand successful product lines',
                'Remove underperforming products'
            ],
            'expected_impact': 'Increase product revenue by 25%',
            'implementation_time': 'Medium-term'
        })

        # Pricing Strategy Recommendations
        recommendations.append({
            'priority': 'High',
            'category': 'Pricing Strategy',
            'title': 'Price Optimization',
            'current_state': 'Current: Fixed pricing',
            'target_state': 'Target: Dynamic pricing',
            'gap': 'Pricing optimization needed',
            'action_items': [
                'Implement competitive price monitoring',
                'Develop dynamic pricing rules',
                'Create volume discount tiers',
                'Optimize shipping thresholds'
            ],
            'expected_impact': 'Increase margins by 10%',
            'implementation_time': 'Short-term'
        })

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        recommendations.append({
            'priority': 'High',
            'category': 'System',
            'title': 'Data Analysis Gap',
            'current_state': 'Limited data analysis',
            'target_state': 'Complete data analysis',
            'gap': 'Unable to perform full analysis',
            'action_items': ['Ensure all data sources are properly connected'],
            'expected_impact': 'Enable complete store analysis',
            'implementation_time': 'Immediate'
        })

    return recommendations

def render_dashboard(store_data):
    """Render the main overview dashboard with enhanced UI"""
    
    # Apply custom CSS
    apply_custom_css()
    
    # Process and cache store data
    processed_data = process_store_data(store_data)
    
    # Dashboard Header
    st.markdown("# 🏪 Store Analytics Dashboard")
    st.markdown("---")
    
    # KPI Metrics Section
    st.markdown('<div class="section-header">📊 Key Metrics</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("💰 Total Sales", f"${processed_data['total_sales']:,.2f}", "Revenue generated from all sales", col1),
        ("📦 Orders", f"{processed_data['total_orders']}", "Total number of orders processed", col2),
        ("💎 Avg Order Value", f"${processed_data['avg_order_value']:,.2f}", "Average value per order", col3),
        ("👥 Active Customers", f"{processed_data['active_customers']}", "Number of active customers", col4)
    ]
    
    for title, value, description, col in metrics:
        with col:
            st.markdown(f"""
                <div class="metric-card animate-fade-in">
                    <h3 style="margin:0; font-size:1rem; color:#666;">{title}</h3>
                    <h2 style="margin:0.5rem 0; font-size:1.8rem; color:#2E86C1;">{value}</h2>
                    <p style="margin:0; font-size:0.8rem; color:#666;">{description}</p>
                </div>
            """, unsafe_allow_html=True)
    
    # Sales Analysis Section
    st.markdown('<div class="section-header">📈 Sales Analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="chart-container">
                <h3 style="margin:0 0 1rem 0; font-size:1.2rem;">📊 Sales Trend</h3>
            </div>
        """, unsafe_allow_html=True)
        sales_chart = create_sales_trend_chart(
            processed_data['daily_sales']['dates'],
            processed_data['daily_sales']['sales']
        )
        st.plotly_chart(sales_chart, use_container_width=True)
    
    with col2:
        st.markdown("""
            <div class="chart-container">
                <h3 style="margin:0 0 1rem 0; font-size:1.2rem;">🔄 Sales by Category</h3>
            </div>
        """, unsafe_allow_html=True)
        category_chart = create_category_chart(processed_data['sales_by_category'])
        st.plotly_chart(category_chart, use_container_width=True)
    
    # Product Analysis Section
    st.markdown('<div class="section-header">📦 Product Analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="chart-container">
                <h3 style="margin:0 0 1rem 0; font-size:1.2rem;">🏆 Top Products</h3>
            </div>
        """, unsafe_allow_html=True)
        st.dataframe(
            processed_data['top_products'],
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.markdown("""
            <div class="chart-container">
                <h3 style="margin:0 0 1rem 0; font-size:1.2rem;">💡 AI Insights</h3>
            </div>
        """, unsafe_allow_html=True)
        for insight in processed_data['customer_insights'][:3]:
            st.markdown(f"""
                <div class="insight-card animate-fade-in">
                    {insight}
                </div>
            """, unsafe_allow_html=True)
    
    # Recommendations Section
    st.markdown('<div class="section-header">🎯 Action Items</div>', unsafe_allow_html=True)
    if processed_data['recommendations']:
        cols = st.columns(3)
        for i, (category, recommendations) in enumerate(list(processed_data['recommendations'].items())[:3]):
            with cols[i % 3]:
                st.markdown(f"""
                    <div class="recommendation-card animate-fade-in">
                        <h4 style="margin:0 0 0.5rem 0; color:#2E86C1;">
                            {category}
                        </h4>
                        {''.join([f'<p style="margin:0.5rem 0;">• {rec}</p>' for rec in recommendations[:2]])}
                    </div>
                """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def render_sales_analysis(store_data):
    """Render the sales analysis page with cached data"""
    processed_data = process_store_data(store_data)
    st.markdown('<div class="section-header">📊 Sales Analysis</div>', unsafe_allow_html=True)
    fig = create_category_chart(processed_data['sales_by_category'])
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl=3600)
def render_product_insights(store_data):
    """Render the product insights page with cached data"""
    processed_data = process_store_data(store_data)
    st.markdown('<div class="section-header">📦 Product Insights</div>', unsafe_allow_html=True)
    st.dataframe(processed_data['top_products'], use_container_width=True)

@st.cache_data(ttl=3600)
def render_customer_analytics(store_data):
    """Render the customer analytics page with cached data"""
    processed_data = process_store_data(store_data)
    st.markdown('<div class="section-header">👥 Customer Analytics</div>', unsafe_allow_html=True)
    fig = px.pie(processed_data['sales_by_channel'], values='sales', names='channel')
    st.plotly_chart(fig, use_container_width=True)

def render_detailed_recommendations(store_data):
    """Render the recommendations page."""
    st.subheader("AI-Powered Recommendations")
    
    if 'recommendations' in store_data:
        for category, recommendations in store_data['recommendations'].items():
            with st.expander(category, expanded=True):
                for rec in recommendations:
                    st.markdown(f"• {rec}")

def render_prediction_page(store_data):
    """Render the predictions page."""
    st.subheader("Sales Predictions")
    st.info("Sales prediction features coming soon!")

def render_metrics_dashboard(data):
    """Render metrics dashboard (placeholder)."""
    st.header("Metrics Dashboard")
    # Add metrics visualization here
    st.write("Metrics dashboard content goes here.")

def format_currency(value):
    """Format currency values."""
    return f"${value:,.2f}"
