#!/bin/bash

# Invoice Intelligence Platform - Setup Script

set -e  # Exit on error

echo "================================================"
echo "Invoice Intelligence Platform - Setup"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check PostgreSQL
echo ""
echo "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL is installed"
    pg_version=$(psql --version | awk '{print $3}')
    echo "Version: $pg_version"
else
    echo "❌ PostgreSQL is not installed"
    echo "Please install PostgreSQL 15+ and try again"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Setup .env file
echo ""
echo "Setting up environment configuration..."
if [ -f ".env" ]; then
    echo ".env file already exists"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✅ .env file created from template"
    fi
else
    cp .env.example .env
    echo "✅ .env file created from template"
fi

# Database setup
echo ""
echo "Database Setup"
echo "---------------"
read -p "Create database 'invoice_db'? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Creating database..."
    psql -U postgres -c "CREATE DATABASE invoice_db;" 2>/dev/null || echo "Database may already exist"
    echo "✅ Database setup complete"
fi

# Run migrations
echo ""
echo "Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"

# Create upload directory
echo ""
echo "Creating upload directory..."
mkdir -p /tmp/invoice_uploads
echo "✅ Upload directory created"

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "⚠️  IMPORTANT: Edit .env file with your NEAR AI API key"
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 - FastAPI Backend:"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "Terminal 2 - Streamlit Dashboard:"
echo "  streamlit run dashboard/app.py --server.port 8501"
echo ""
echo "Access the dashboard at: http://localhost:8501"
echo "Access API docs at: http://localhost:8000/docs"
echo ""
