#!/bin/bash

# Azure App Service startup script for Python FastAPI application

# Activate virtual environment if it exists (Azure creates one automatically)
if [ -d /home/site/wwwroot/antenv ]; then
    source /home/site/wwwroot/antenv/bin/activate
fi

# Navigate to application directory
cd /home/site/wwwroot

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application on 0.0.0.0:8000..."
python main.py
