#!/bin/bash

# Set OpenMP environment variables
export LDFLAGS="-L/usr/local/opt/libomp/lib"
export CPPFLAGS="-I/usr/local/opt/libomp/include"

# Activate virtual environment
source venv/bin/activate

# Install/upgrade requirements
pip install -r requirements.txt

# Run the application
streamlit run main.py 