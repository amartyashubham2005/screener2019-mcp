#!/bin/bash

# Azure App Service startup script for Python FastAPI application
# NOTE: Oryx calls this script from the extracted directory (/tmp/<hash>)
# So we use the current working directory as the app path

echo "=== Azure App Service Startup Script ==="
echo "Current directory: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"

# The current working directory is where Oryx extracted our app
APP_PATH="$(pwd)"
echo "Using application path: $APP_PATH"

# List directory contents for debugging
echo "Directory contents:"
ls -la

# The virtual environment should already be activated by Oryx's wrapper script
# But let's verify and activate if needed
VENV_PATH="$APP_PATH/antenv"
if [ -d "$VENV_PATH" ]; then
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Activating virtual environment at: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
    else
        echo "Virtual environment already activated: $VIRTUAL_ENV"
    fi
else
    echo "WARNING: Virtual environment not found at $VENV_PATH"
    echo "Looking for antenv in parent directories..."
    find /tmp -name "antenv" -type d 2>/dev/null | head -5
fi

# Verify Python environment
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Check if requirements.txt exists and install dependencies
if [ -f "requirements.txt" ]; then
    echo "Found requirements.txt, installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found in $APP_PATH"
    echo "Skipping dependency installation (may already be installed by Oryx)"
fi

# Run database migrations
if [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    alembic upgrade head || echo "WARNING: Database migration failed"
else
    echo "WARNING: alembic.ini not found at $APP_PATH/alembic.ini"
    echo "Skipping migrations"
fi

# Start the application
if [ -f "main.py" ]; then
    echo "Starting application on 0.0.0.0:8000..."
    exec python main.py
else
    echo "ERROR: main.py not found in $APP_PATH"
    echo "Full directory listing:"
    ls -laR
    exit 1
fi
