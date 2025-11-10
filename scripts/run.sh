#!/bin/bash

echo "Multilevel Queue Scheduling Simulator - MySQL Version"
echo "===================================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if MySQL is running
if ! systemctl is-active --quiet mysql 2>/dev/null; then
    echo "MySQL is not running. Please start MySQL service."
    echo "On Windows with XAMPP: Start Apache and MySQL from XAMPP Control Panel"
    echo "On Linux: sudo systemctl start mysql"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    python -m venv backend/venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source backend/venv/Scripts/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

# Initialize database (this will create tables if they don't exist)
echo "Initializing database..."
python -c "
from database import Database
db = Database()
print('Database setup completed!')
"

# Start the Flask application
echo "Starting MLQ Scheduling Simulator..."
echo "Application will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the application"

python backend/app.py

# Deactivate virtual environment
deactivate

echo "Application stopped."