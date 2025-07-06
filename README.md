# Fraud Detection System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

A comprehensive fraud detection system that mimics professional fraud analyst workflows using behavioral analytics, correlation rules, and machine learning. This system provides a complete solution for detecting, analyzing, and investigating potentially fraudulent transactions.

## Features

- **Machine Learning Detection**: Advanced anomaly detection using trained ML models
- **Behavioral Pattern Analysis**: Identify unusual user behaviors and transaction patterns
- **Rule-Based Correlation Engine**: Configurable rules for fraud detection
- **Interactive Dashboard**: Complete investigation interface with data visualization
- **Risk Scoring System**: Multi-factor risk assessment with explainable results
- **Transaction Monitoring**: Real-time monitoring and alerting capabilities
- **Case Management**: Track and manage fraud investigations

## Screenshots

*(Add screenshots of your dashboard here)*

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Setup

1. Clone the repository:
   ```
   git https://github.com/krishna-1230/fraud_detection_sys.git
   cd fraud-detection-system
   ```

2. Create and activate a virtual environment:
   ```
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```
   python scripts/setup_database.py
   ```

## Usage

### Running the Application

You can run the application using either:

```
python run.py
```

Or on Windows, you can use the batch file:

```
run_frauddetection.bat
```

### Accessing the Dashboard

Once running, access the dashboard at:
```
http://127.0.0.1:8050/
```

### Key Dashboard Features

- **Overview**: High-level metrics and trends
- **Transactions**: Search, filter, and investigate individual transactions
- **Alerts**: Review and manage triggered fraud alerts
- **Rules**: Configure and monitor rule performance
- **Analytics**: Advanced data exploration and visualization

## Project Structure

```
fraud-detection-system/
│
├── app.py                 # Main Dash application with dashboard
├── run.py                 # Setup and execution script
├── run_frauddetection.bat # Windows batch file for easy execution
│
├── dashboard/             # Dashboard UI components
│   ├── layouts.py         # Dashboard layout definitions
│   └── components.py      # Reusable UI components
│
├── models/                # Machine learning models
│   ├── fraud_detector.py  # Fraud detection model implementation
│   └── fraud_model.joblib # Trained model file
│
├── rules/                 # Rule-based detection
│   └── rules_engine.py    # Rules implementation and execution
│
├── data/                  # Data storage and processing
│   └── (sample data files)
│
├── utils/                 # Utility functions
│   └── data_utils.py      # Data processing utilities
│
├── scripts/               # Setup and maintenance scripts
│   ├── setup_database.py  # Database initialization
│   └── generate_data.py   # Synthetic data generation
│
├── db/                    # Database files
│   └── fraud_detection.db # SQLite database (created on setup)
│
└── tests/                 # Unit and integration tests
```

## Development

### Adding New Rules

To add new fraud detection rules, modify the `rules/rules_engine.py` file:

1. Define a new rule function
2. Add the rule to the rules registry
3. Specify rule parameters and thresholds

### Extending the ML Model

To enhance the machine learning capabilities:

1. Add new features in `models/fraud_detector.py`
2. Retrain the model using updated training data
3. Evaluate performance using the built-in metrics

## Testing

Run the test suite:

```
pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Dash](https://dash.plotly.com/) and [Plotly](https://plotly.com/)
- Uses [scikit-learn](https://scikit-learn.org/) for machine learning components
