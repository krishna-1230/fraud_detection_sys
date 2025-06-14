# Fraud Detection System MVP

An advanced fraud detection system that mimics professional fraud analyst workflows using behavioral analytics, correlation rules, and machine learning.

## Features

- Transaction anomaly detection using machine learning
- Behavioral pattern analysis 
- Rule-based correlation engine
- Interactive dashboard for fraud investigation
- Risk scoring system

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Set up the database:
```
python scripts/setup_database.py
```

3. Run the application:
```
python app.py
```

4. Access the dashboard at http://127.0.0.1:8050/

## Project Structure

- `app.py`: Main application with Dash dashboard
- `models/`: ML models for fraud detection
- `data/`: Sample data and data processing scripts
- `utils/`: Utility functions
- `rules/`: Fraud detection rules
- `dashboard/`: Dashboard components
- `scripts/`: Database setup and maintenance scripts "# fraud_detection_sys" 
