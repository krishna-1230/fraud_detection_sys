import pandas as pd
import numpy as np
import sqlite3
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
from sklearn.impute import SimpleImputer
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

class FraudDetector:
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(os.path.dirname(__file__), "fraud_model.joblib")
        self.feature_importance = None
    
    def load_data(self):
        """Load transaction data from database with user and merchant features"""
        conn = sqlite3.connect("db/fraud_detection.db")
        
        # Fetch transactions and join with user and merchant data
        query = """
        SELECT 
            t.transaction_id, t.user_id, t.amount, t.timestamp,
            t.merchant_category, t.country, t.device_id, t.ip_address, t.is_fraud,
            u.account_age_days, u.country_of_residence, u.num_payment_methods,
            u.account_type, u.has_verified_email, u.has_verified_phone, u.risk_score
        FROM transactions t
        JOIN users u ON t.user_id = u.user_id
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def preprocess_data(self, df):
        """Preprocess data for model training"""
        # Feature engineering
        
        # Extract time features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
        
        # Device features
        df['new_device'] = df['device_id'].apply(lambda x: 1 if 'NEW' in x else 0)
        
        # IP features
        df['suspicious_ip'] = df['ip_address'].apply(lambda x: 0 if x.startswith('192.168') else 1)
        
        # Country match feature
        df['country_match'] = (df['country'] == df['country_of_residence']).astype(int)
        
        # Drop non-numeric and identifier columns
        drop_cols = ['transaction_id', 'user_id', 'timestamp', 'device_id', 'ip_address']
        
        # Define features and target
        X = df.drop(drop_cols + ['is_fraud'], axis=1)
        y = df['is_fraud']
        
        # Define categorical and numerical columns
        categorical_cols = ['merchant_category', 'country', 'country_of_residence', 'account_type']
        numeric_cols = [col for col in X.columns if col not in categorical_cols]
        
        return X, y, categorical_cols, numeric_cols
    
    def build_model(self, X, y, categorical_cols, numeric_cols):
        """Build and train the machine learning model"""
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Define preprocessing steps
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        # Combine preprocessing steps
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_cols),
                ('cat', categorical_transformer, categorical_cols)
            ])
        
        # Define model pipeline
        model_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', GradientBoostingClassifier(random_state=42))
        ])
        
        # Define parameter grid for hyperparameter tuning
        param_grid = {
            'classifier__n_estimators': [100, 200],
            'classifier__learning_rate': [0.05, 0.1],
            'classifier__max_depth': [3, 5]
        }
        
        # Perform grid search
        print("Performing hyperparameter optimization...")
        grid_search = GridSearchCV(
            model_pipeline, param_grid, cv=3, 
            scoring='roc_auc', n_jobs=-1
        )
        
        grid_search.fit(X_train, y_train)
        best_model = grid_search.best_estimator_
        
        # Evaluate model on test data
        y_pred_proba = best_model.predict_proba(X_test)[:, 1]
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        # Get prediction at threshold 0.5
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        print("\nModel Performance:")
        print(f"AUC Score: {auc_score:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save feature importances if using tree-based model
        if hasattr(best_model['classifier'], 'feature_importances_'):
            # Get feature names after one-hot encoding
            ohe = best_model.named_steps['preprocessor'].named_transformers_['cat'].named_steps['onehot']
            feature_names = numeric_cols + list(ohe.get_feature_names_out(categorical_cols))
            
            # Get feature importances
            importances = best_model['classifier'].feature_importances_
            
            # Store feature importances
            self.feature_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
        
        # Store model
        self.model = best_model
        
        return self.model, X_test, y_test
    
    def save_model(self):
        """Save model to disk"""
        if self.model is None:
            print("No model to save.")
            return
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print(f"Model saved to {self.model_path}")
        
        # Save feature importances
        if self.feature_importance is not None:
            importance_path = os.path.join(os.path.dirname(__file__), "feature_importance.csv")
            self.feature_importance.to_csv(importance_path, index=False)
            print(f"Feature importance saved to {importance_path}")
    
    def load_model(self):
        """Load model from disk"""
        if not os.path.exists(self.model_path):
            print("No saved model found.")
            return None
        
        self.model = joblib.load(self.model_path)
        print(f"Model loaded from {self.model_path}")
        
        # Load feature importances if available
        importance_path = os.path.join(os.path.dirname(__file__), "feature_importance.csv")
        if os.path.exists(importance_path):
            self.feature_importance = pd.read_csv(importance_path)
        
        return self.model
    
    def predict(self, transaction_data):
        """Make predictions on new transaction data"""
        if self.model is None:
            self.load_model()
            
            if self.model is None:
                print("No model available for prediction.")
                return None
        
        # Prepare data
        if isinstance(transaction_data, pd.DataFrame):
            # If multiple rows are provided
            predictions = self.model.predict_proba(transaction_data)[:, 1]
        else:
            # For single transaction (as dict)
            df = pd.DataFrame([transaction_data])
            predictions = self.model.predict_proba(df)[:, 1]
            predictions = predictions[0]
        
        return predictions

    def update_transaction_scores(self):
        """Update ML risk scores for all transactions in the database"""
        conn = sqlite3.connect("db/fraud_detection.db")
        
        # Get transaction data
        df = self.load_data()
        
        # Preprocess data (excluding the target variable)
        X, _, categorical_cols, numeric_cols = self.preprocess_data(df)
        
        # Make predictions
        if self.model is None:
            self.load_model()
        
        if self.model is not None:
            # Get risk scores
            df['ml_score'] = self.model.predict_proba(X)[:, 1]
            
            # Update database
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute(
                    """
                    UPDATE transactions 
                    SET ml_score = ? 
                    WHERE transaction_id = ?
                    """,
                    (row['ml_score'], row['transaction_id'])
                )
            
            conn.commit()
            print(f"Updated ML scores for {len(df)} transactions")
        
        conn.close()
        
def train_model():
    """Train and save a fraud detection model"""
    detector = FraudDetector()
    
    print("Loading data...")
    df = detector.load_data()
    
    print("Preprocessing data...")
    X, y, categorical_cols, numeric_cols = detector.preprocess_data(df)
    
    print("Training model...")
    model, X_test, y_test = detector.build_model(X, y, categorical_cols, numeric_cols)
    
    print("Saving model...")
    detector.save_model()
    
    # Update all transaction scores in the database
    print("Updating transaction scores...")
    detector.update_transaction_scores()
    
    return detector

if __name__ == "__main__":
    train_model() 