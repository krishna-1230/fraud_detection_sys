import sqlite3
import os
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def setup_database():
    """Create SQLite database and necessary tables"""
    
    # Create db directory if it doesn't exist
    os.makedirs("db", exist_ok=True)
    
    # Connect to SQLite database (creates file if it doesn't exist)
    conn = sqlite3.connect("db/fraud_detection.db")
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        amount REAL NOT NULL,
        merchant_category TEXT NOT NULL,
        country TEXT NOT NULL,
        device_id TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        is_fraud INTEGER NOT NULL,
        ml_score REAL,
        rule_score REAL,
        final_risk_score REAL,
        reviewed INTEGER DEFAULT 0,
        review_notes TEXT
    )
    ''')
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        account_age_days INTEGER NOT NULL,
        country_of_residence TEXT NOT NULL,
        num_payment_methods INTEGER NOT NULL,
        account_type TEXT NOT NULL,
        has_verified_email INTEGER NOT NULL,
        has_verified_phone INTEGER NOT NULL,
        risk_score REAL NOT NULL
    )
    ''')
    
    # Create merchants table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS merchants (
        merchant_id TEXT PRIMARY KEY,
        merchant_name TEXT NOT NULL,
        merchant_category TEXT NOT NULL,
        country TEXT NOT NULL,
        average_transaction_amount REAL NOT NULL,
        merchant_risk_score REAL NOT NULL
    )
    ''')
    
    # Create rules table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rules (
        rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        query TEXT NOT NULL,
        risk_weight REAL NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Create alerts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT NOT NULL,
        rule_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        risk_score REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        assigned_to TEXT,
        resolution TEXT,
        FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id),
        FOREIGN KEY (rule_id) REFERENCES rules (rule_id)
    )
    ''')
    
    # Commit the changes
    conn.commit()
    
    # Create indices for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions (timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_is_fraud ON transactions (is_fraud)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status)')
    
    conn.commit()
    conn.close()
    
    print("Database setup complete")
    
def load_data():
    """Load data from CSV files into database"""
    # Check if the CSV files exist
    if not os.path.exists("data/transactions.csv") or \
       not os.path.exists("data/users.csv") or \
       not os.path.exists("data/merchants.csv"):
        print("CSV data files not found. Run generate_data.py first.")
        return
    
    # Load data from CSV
    transactions_df = pd.read_csv("data/transactions.csv")
    users_df = pd.read_csv("data/users.csv")
    merchants_df = pd.read_csv("data/merchants.csv")
    
    # Connect to database
    conn = sqlite3.connect("db/fraud_detection.db")
    
    # Load data into tables
    transactions_df.to_sql("transactions", conn, if_exists="replace", index=False)
    users_df.to_sql("users", conn, if_exists="replace", index=False)
    merchants_df.to_sql("merchants", conn, if_exists="replace", index=False)
    
    # Add initial rules
    create_rules(conn)
    
    conn.close()
    
    print(f"Loaded {len(transactions_df)} transactions")
    print(f"Loaded {len(users_df)} users")
    print(f"Loaded {len(merchants_df)} merchants")
    print("Data loaded into database successfully")

def create_rules(conn):
    """Create initial fraud detection rules"""
    cursor = conn.cursor()
    
    # Delete existing rules
    cursor.execute("DELETE FROM rules")
    
    # List of rules
    rules = [
        (
            "High Amount Transaction", 
            "Transaction amount significantly higher than average",
            """
            SELECT t.transaction_id, t.user_id, t.amount, t.timestamp, t.merchant_category, t.country
            FROM transactions t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.amount > 1000
            AND t.reviewed = 0
            ORDER BY t.amount DESC
            """,
            0.7
        ),
        (
            "Foreign Transaction", 
            "Transaction in a country different from user's country of residence",
            """
            SELECT t.transaction_id, t.user_id, t.amount, t.timestamp, t.merchant_category, t.country, 
                   u.country_of_residence
            FROM transactions t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.country != u.country_of_residence
            AND t.reviewed = 0
            """,
            0.6
        ),
        (
            "New Device", 
            "Transaction from a device ID not previously associated with the user",
            """
            SELECT t1.transaction_id, t1.user_id, t1.amount, t1.timestamp, 
                   t1.merchant_category, t1.device_id
            FROM transactions t1
            WHERE t1.device_id LIKE 'NEW%'
            AND t1.reviewed = 0
            """,
            0.5
        ),
        (
            "Rapid Succession", 
            "Multiple transactions by the same user within a short time period",
            """
            SELECT t1.transaction_id, t1.user_id, t1.amount, t1.timestamp,
                   t1.merchant_category, t2.transaction_id as related_transaction,
                   t2.timestamp as related_timestamp
            FROM transactions t1
            JOIN transactions t2 ON t1.user_id = t2.user_id
            WHERE t1.transaction_id != t2.transaction_id
            AND datetime(t1.timestamp) <= datetime(t2.timestamp, '+1 hour')
            AND datetime(t1.timestamp) >= datetime(t2.timestamp, '-1 hour')
            AND t1.reviewed = 0
            GROUP BY t1.transaction_id
            HAVING COUNT(*) >= 3
            """,
            0.6
        ),
        (
            "High-Risk Merchant Category", 
            "Transaction with merchant category known for high fraud rates",
            """
            SELECT t.transaction_id, t.user_id, t.amount, t.timestamp, t.merchant_category
            FROM transactions t
            WHERE t.merchant_category IN ('gambling', 'crypto', 'money_transfer', 'jewelry')
            AND t.reviewed = 0
            """,
            0.5
        ),
        (
            "Multiple Countries", 
            "Transactions from same user in multiple countries in a short time period",
            """
            SELECT t1.transaction_id, t1.user_id, t1.country, t1.timestamp,
                   t2.transaction_id as related_transaction, t2.country as related_country,
                   t2.timestamp as related_timestamp
            FROM transactions t1
            JOIN transactions t2 ON t1.user_id = t2.user_id
            WHERE t1.country != t2.country
            AND t1.transaction_id != t2.transaction_id
            AND datetime(t1.timestamp) <= datetime(t2.timestamp, '+24 hours')
            AND datetime(t1.timestamp) >= datetime(t2.timestamp, '-24 hours')
            AND t1.reviewed = 0
            """,
            0.8
        ),
        (
            "Unusual Merchant for User", 
            "Transaction with merchant category not typically used by the user",
            """
            SELECT t1.transaction_id, t1.user_id, t1.merchant_category, 
                   COUNT(*) as transaction_count
            FROM transactions t1
            LEFT JOIN (
                SELECT user_id, merchant_category, COUNT(*) as category_count
                FROM transactions
                GROUP BY user_id, merchant_category
                HAVING COUNT(*) > 2
            ) t2 ON t1.user_id = t2.user_id AND t1.merchant_category = t2.merchant_category
            WHERE t2.user_id IS NULL
            AND t1.reviewed = 0
            GROUP BY t1.user_id, t1.merchant_category
            """,
            0.4
        )
    ]
    
    # Insert rules
    cursor.executemany(
        """
        INSERT INTO rules (name, description, query, risk_weight, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """, 
        [(*rule, ) for rule in rules]
    )
    
    # Commit the changes
    conn.commit()
    
    print(f"Created {len(rules)} detection rules")

def main():
    # Setup database structure
    setup_database()
    
    # Generate data if it doesn't exist
    if not os.path.exists("data/transactions.csv"):
        print("Generating sample data...")
        try:
            from generate_data import main as generate_data_main
            generate_data_main()
        except Exception as e:
            print(f"Error generating data: {e}")
            return
    
    # Load data into database
    load_data()
    
    print("Database initialized successfully")

if __name__ == "__main__":
    main() 