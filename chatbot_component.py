"""Optimized chatbot component with improved responsiveness."""

import streamlit as st
from openai import OpenAI
import json
import os
from datetime import datetime
import asyncio
import concurrent.futures
from functools import lru_cache

# Initialize OpenAI client at module level
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Cache for storing recent responses
@lru_cache(maxsize=100)
def cache_response(question_hash, context_hash):
    """Cache responses to avoid redundant API calls."""
    return f"Cached response for {question_hash}"

@st.cache_data(ttl=3600)
def get_store_context(store_data):
    """Cache store context to avoid regenerating it."""
    return f"""
Store Metrics:
- Total Sales: ${store_data['total_sales']:,.2f}
- Total Orders: {store_data['total_orders']}
- Average Order Value: ${store_data['avg_order_value']:,.2f}
- Active Customers: {store_data['active_customers']}
"""

async def get_ai_response(question, context):
    """Asynchronously get response from OpenAI."""
    try:
        # Create a unique hash for caching
        question_hash = hash(question)
        context_hash = hash(context)
        
        # Check cache first
        cached = cache_response(question_hash, context_hash)
        if cached:
            return cached

        # If not in cache, make API call
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": question}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def render_message(message, is_user):
    """Render a single chat message with optimized styling."""
    message_type = "user" if is_user else "assistant"
    alignment = "right" if is_user else "left"
    
    st.markdown(f"""
        <div class="chat-message {message_type}-message" style="text-align: {alignment}">
            <div class="message-content">
                <strong>{'You' if is_user else 'Assistant'}:</strong> {message}
            </div>
            <div class="message-timestamp" style="font-size: 0.8em; color: #666;">
                {datetime.now().strftime('%H:%M')}
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_chatbot(store_data):
    """Render the optimized chatbot interface."""
    st.markdown("""
        <style>
        .chat-container {
            height: 600px;
            overflow-y: auto;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .chat-message {
            padding: 0.8rem;
            border-radius: 15px;
            margin: 0.5rem 0;
            max-width: 80%;
            animation: fadeIn 0.3s ease-in-out;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: auto;
        }
        .assistant-message {
            background-color: #ffffff;
            margin-right: auto;
        }
        .message-content {
            word-wrap: break-word;
        }
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        .quick-action-button {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 20px;
            padding: 0.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .quick-action-button:hover {
            background-color: #e9ecef;
            transform: translateY(-2px);
        }
        .stTextInput > div > div > input {
            border-radius: 20px;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Quick action buttons
    st.markdown("### 💬 Store Analytics Assistant")
    
    quick_actions = [
        {"icon": "📊", "label": "Sales", "question": "What are the total sales?"},
        {"icon": "📈", "label": "Trends", "question": "What are the current sales trends?"},
        {"icon": "🏆", "label": "Top Products", "question": "What are our top products?"},
        {"icon": "👥", "label": "Customers", "question": "How many active customers do we have?"}
    ]

    cols = st.columns(len(quick_actions))
    for idx, (col, action) in enumerate(zip(cols, quick_actions)):
        with col:
            if st.button(
                f"{action['icon']} {action['label']}", 
                key=f"quick_action_{idx}",
                use_container_width=True
            ):
                st.session_state.chat_history.append({
                    "is_user": True,
                    "message": action["question"]
                })
                
                # Get response asynchronously
                with st.spinner(""):
                    context = get_store_context(store_data)
                    response = asyncio.run(get_ai_response(action["question"], context))
                    st.session_state.chat_history.append({
                        "is_user": False,
                        "message": response
                    })
                st.rerun()

    # Chat history container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.chat_history:
        render_message(message["message"], message["is_user"])
    st.markdown('</div>', unsafe_allow_html=True)

    # User input
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="Type your question here...",
                label_visibility="collapsed",
                key="user_input"
            )
        with col2:
            submit_button = st.form_submit_button("Send", use_container_width=True)

        if submit_button and user_input.strip():
            st.session_state.chat_history.append({
                "is_user": True,
                "message": user_input
            })
            
            # Get response asynchronously
            with st.spinner(""):
                context = get_store_context(store_data)
                response = asyncio.run(get_ai_response(user_input, context))
                st.session_state.chat_history.append({
                    "is_user": False,
                    "message": response
                })
            st.rerun()

    # Clear chat button
    if st.button("Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun() 