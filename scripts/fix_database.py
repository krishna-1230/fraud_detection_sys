import sqlite3
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def fix_database():
    print('Fixing database schema...')
    conn = sqlite3.connect("db/fraud_detection.db")
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
    if not cursor.fetchone():
        print("Error: transactions table doesn't exist")
        conn.close()
        return False

    # Check and add missing columns
    cursor.execute('PRAGMA table_info(transactions)')
    columns = [col[1] for col in cursor.fetchall()]

    # Add ml_score if missing
    if 'ml_score' not in columns:
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN ml_score REAL')
            print('Added ml_score column')
        except sqlite3.OperationalError as e:
            print(f'Error adding ml_score: {e}')

    # Add rule_score if missing
    if 'rule_score' not in columns:
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN rule_score REAL')
            print('Added rule_score column')
        except sqlite3.OperationalError as e:
            print(f'Error adding rule_score: {e}')

    # Add final_risk_score if missing
    if 'final_risk_score' not in columns:
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN final_risk_score REAL')
            print('Added final_risk_score column')
        except sqlite3.OperationalError as e:
            print(f'Error adding final_risk_score: {e}')

    # Add reviewed and review_notes if missing
    if 'reviewed' not in columns:
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN reviewed INTEGER DEFAULT 0')
            print('Added reviewed column')
        except sqlite3.OperationalError as e:
            print(f'Error adding reviewed: {e}')

    if 'review_notes' not in columns:
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN review_notes TEXT')
            print('Added review_notes column')
        except sqlite3.OperationalError as e:
            print(f'Error adding review_notes: {e}')

    conn.commit()
    conn.close()
    print('Database fix complete')
    return True

if __name__ == "__main__":
    fix_database() 