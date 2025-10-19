#!/bin/bash

# Azure App Service startup script for Python FastAPI application

# Oryx extracts to /tmp during deployment. This script works with Oryx paths.
# Reference: Azure logs show "App path is set to '/tmp/<hash>'"

# Find the Oryx-extracted application directory
# Oryx sets PYTHONPATH which includes the extracted app path
APP_PATH="/home/site/wwwroot"

# Check if Oryx extracted to /tmp (look for antenv in common locations)
if [ -n "$PYTHONPATH" ]; then
    # Extract app path from PYTHONPATH (format: /opt/startup/app_logs:/tmp/<hash>/antenv/lib/python3.12/site-packages)
    EXTRACTED_PATH=$(echo "$PYTHONPATH" | grep -oP '/tmp/[^/]+(?=/antenv)' | head -n 1)
    if [ -n "$EXTRACTED_PATH" ] && [ -d "$EXTRACTED_PATH" ]; then
        echo "Found Oryx extracted path: $EXTRACTED_PATH"
        APP_PATH="$EXTRACTED_PATH"
    fi
fi

echo "Using application path: $APP_PATH"

# Activate virtual environment
VENV_PATH="$APP_PATH/antenv"
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment at: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
else
    echo "WARNING: Virtual environment not found at $VENV_PATH"
fi

# Navigate to application directory
cd "$APP_PATH"
echo "Current directory: $(pwd)"

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing/upgrading dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found in $APP_PATH"
fi

# Run database migrations
if [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    alembic upgrade head || echo "FAILED: Database migration failed"
else
    echo "WARNING: alembic.ini not found, skipping migrations"
fi

# Start the application
if [ -f "main.py" ]; then
    echo "Starting application on 0.0.0.0:8000..."
    python main.py
else
    echo "ERROR: main.py not found in $APP_PATH"
    echo "Directory contents:"
    ls -la
    exit 1
fi
