"""
Fraud Detection System MVP - Setup and Run script

This script handles the complete setup and launching of the fraud detection system.
It will:
1. Generate synthetic data
2. Set up the database
3. Train the ML model
4. Run the rules engine
5. Start the Dash application

Usage:
    python run.py
"""

import os
import subprocess
import sys
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    print("Checking requirements...")
    try:
        import pandas
        import numpy
        import plotly
        import dash
        import dash_bootstrap_components
        import sklearn
        import sqlalchemy
        import joblib
        print("All requirements available.")
        return True
    except ImportError as e:
        print(f"Missing requirement: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_database():
    """Run database setup script"""
    print("Setting up database...")
    try:
        subprocess.run([sys.executable, "scripts/setup_database.py"], check=True)
        print("Database setup complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Database setup failed: {e}")
        return False

def train_model():
    """Train the fraud detection model"""
    print("Training fraud detection model...")
    try:
        from models.fraud_detector import train_model
        model = train_model()
        print("Model training complete.")
        return True
    except Exception as e:
        print(f"Model training failed: {e}")
        return False

def run_rules_engine():
    """Run the rules engine to evaluate transactions"""
    print("Running rules engine...")
    try:
        from rules.rules_engine import run_rules_engine
        engine = run_rules_engine()
        print("Rules engine complete.")
        return True
    except Exception as e:
        print(f"Rules engine failed: {e}")
        return False

def start_application():
    """Start the Dash web application"""
    print("Starting fraud detection dashboard...")
    try:
        from app import app
        print("Dashboard running at http://127.0.0.1:8050/")
        app.run_server(debug=False, host="0.0.0.0", port=8050)
        return True
    except Exception as e:
        print(f"Application startup failed: {e}")
        return False

def main():
    """Main execution function"""
    # Add project root to path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    print("Fraud Detection System MVP Setup")
    print("================================")
    
    # Check requirements first
    if not check_requirements():
        return False
    
    # Create necessary directories
    os.makedirs("db", exist_ok=True)
    
    # Check if database exists
    if not os.path.exists("db/fraud_detection.db"):
        # Database doesn't exist, perform setup
        if not setup_database():
            return False
        
        # Train ML model
        if not train_model():
            return False
        
        # Run rules engine
        if not run_rules_engine():
            return False
    
    # Start the web application
    start_application()
    
    return True

if __name__ == "__main__":
    main() 