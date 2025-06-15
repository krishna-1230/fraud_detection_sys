import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

class RulesEngine:
    def __init__(self):
        self.rules = []
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect("db/fraud_detection.db")
        self.cursor = self.conn.cursor()
        
    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def load_rules(self):
        """Load rules from the database"""
        if not self.conn:
            self.connect_db()
            
        # Get active rules
        self.cursor.execute(
            "SELECT rule_id, name, description, query, risk_weight FROM rules WHERE is_active = 1"
        )
        
        self.rules = [{
            'rule_id': row[0],
            'name': row[1],
            'description': row[2],
            'query': row[3],
            'risk_weight': row[4]
        } for row in self.cursor.fetchall()]
        
        print(f"Loaded {len(self.rules)} active rules")
        
        return self.rules
    
    def evaluate_transaction(self, transaction_id):
        """
        Evaluate a single transaction against all rules
        Returns a list of triggered rules
        """
        if not self.conn:
            self.connect_db()
            
        if not self.rules:
            self.load_rules()
        
        triggered_rules = []
        
        for rule in self.rules:
            # Execute the rule query with transaction_id parameter
            modified_query = f"{rule['query']} AND t.transaction_id = ?"
            
            # Execute query
            self.cursor.execute(modified_query, (transaction_id,))
            results = self.cursor.fetchall()
            
            if results:
                triggered_rules.append({
                    'rule_id': rule['rule_id'],
                    'name': rule['name'],
                    'description': rule['description'],
                    'risk_weight': rule['risk_weight']
                })
        
        return triggered_rules
    
    def evaluate_all_transactions(self):
        """
        Evaluate all transactions against all rules
        Update rule_score in the transactions table
        Create alerts for triggered rules
        """
        if not self.conn:
            self.connect_db()
            
        if not self.rules:
            self.load_rules()
        
        print("Evaluating transactions against rules...")
        
        # Get all transaction IDs
        self.cursor.execute("SELECT transaction_id FROM transactions")
        transaction_ids = [row[0] for row in self.cursor.fetchall()]
        
        # Create dictionary to store rule scores
        rule_scores = {}
        total_alerts = 0
        
        # Process each transaction
        for transaction_id in transaction_ids:
            triggered_rules = []
            
            # Check each rule against the transaction
            for rule in self.rules:
                # Modify query to check for specific transaction
                base_query = rule['query']
                
                # Determine the table alias used in the query
                if "t1." in base_query:
                    table_alias = "t1"
                else:
                    table_alias = "t"
                
                # Make sure query has a WHERE clause
                if "WHERE" in base_query:
                    # Add transaction_id condition
                    parts = base_query.split("WHERE", 1)
                    modified_query = f"{parts[0]} WHERE {parts[1]} AND {table_alias}.transaction_id = '{transaction_id}'"
                else:
                    modified_query = f"{base_query} WHERE {table_alias}.transaction_id = '{transaction_id}'"
                
                # Remove ORDER BY clause if present as it can cause issues with AND condition
                if "ORDER BY" in modified_query:
                    modified_query = modified_query.split("ORDER BY")[0]
                
                # Execute modified query
                try:
                    self.cursor.execute(modified_query)
                    results = self.cursor.fetchall()
                    
                    if results:
                        triggered_rules.append({
                            'rule_id': rule['rule_id'],
                            'risk_weight': rule['risk_weight']
                        })
                        
                        # Create alert
                        self.cursor.execute(
                            """
                            INSERT INTO alerts (transaction_id, rule_id, created_at, risk_score, status)
                            VALUES (?, ?, datetime('now'), ?, 'open')
                            """,
                            (transaction_id, rule['rule_id'], rule['risk_weight'])
                        )
                        total_alerts += 1
                except sqlite3.Error as e:
                    print(f"Error executing rule {rule['name']} for transaction {transaction_id}: {e}")
                    print(f"Query: {modified_query}")
            
            # Calculate rule score as sum of weights of triggered rules
            if triggered_rules:
                rule_score = min(1.0, sum(r['risk_weight'] for r in triggered_rules))
                rule_scores[transaction_id] = rule_score
        
        # Update rule scores in database
        for transaction_id, rule_score in rule_scores.items():
            self.cursor.execute(
                "UPDATE transactions SET rule_score = ? WHERE transaction_id = ?",
                (rule_score, transaction_id)
            )
        
        # Update final risk scores (combining ML and rule scores)
        self.cursor.execute(
            """
            UPDATE transactions
            SET final_risk_score = CASE
                WHEN ml_score IS NULL THEN rule_score
                WHEN rule_score IS NULL THEN ml_score
                ELSE (ml_score + rule_score) / 2
            END
            WHERE ml_score IS NOT NULL OR rule_score IS NOT NULL
            """
        )
        
        self.conn.commit()
        print(f"Updated rule scores for {len(rule_scores)} transactions")
        print(f"Created {total_alerts} alerts")
    
    def get_rule_counts(self):
        """Get count of alerts per rule"""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute(
            """
            SELECT r.rule_id, r.name, COUNT(a.alert_id) as alert_count
            FROM rules r
            LEFT JOIN alerts a ON r.rule_id = a.rule_id
            GROUP BY r.rule_id, r.name
            ORDER BY alert_count DESC
            """
        )
        
        return [{
            'rule_id': row[0],
            'name': row[1],
            'alert_count': row[2]
        } for row in self.cursor.fetchall()]

    def get_high_risk_transactions(self, threshold=0.7, limit=100):
        """Get high-risk transactions based on final risk score"""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute(
            """
            SELECT t.transaction_id, t.user_id, t.timestamp, t.amount, 
                   t.merchant_category, t.country, t.final_risk_score,
                   t.is_fraud, COUNT(a.alert_id) as alert_count
            FROM transactions t
            LEFT JOIN alerts a ON t.transaction_id = a.transaction_id
            WHERE t.final_risk_score >= ?
            GROUP BY t.transaction_id
            ORDER BY t.final_risk_score DESC, alert_count DESC
            LIMIT ?
            """,
            (threshold, limit)
        )
        
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def get_alerts_by_transaction(self, transaction_id):
        """Get all alerts for a specific transaction"""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute(
            """
            SELECT a.alert_id, r.name as rule_name, r.description, a.created_at, 
                   a.risk_score, a.status
            FROM alerts a
            JOIN rules r ON a.rule_id = r.rule_id
            WHERE a.transaction_id = ?
            ORDER BY a.risk_score DESC
            """,
            (transaction_id,)
        )
        
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update_alert_status(self, alert_id, status, resolution=None):
        """Update the status of an alert"""
        if not self.conn:
            self.connect_db()
        
        if resolution:
            self.cursor.execute(
                """
                UPDATE alerts
                SET status = ?, resolution = ?
                WHERE alert_id = ?
                """,
                (status, resolution, alert_id)
            )
        else:
            self.cursor.execute(
                """
                UPDATE alerts
                SET status = ?
                WHERE alert_id = ?
                """,
                (status, alert_id)
            )
        
        self.conn.commit()
        return True
    
    def update_transaction_review(self, transaction_id, reviewed=True, notes=None):
        """Mark a transaction as reviewed"""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute(
            """
            UPDATE transactions
            SET reviewed = ?, review_notes = ?
            WHERE transaction_id = ?
            """,
            (1 if reviewed else 0, notes, transaction_id)
        )
        
        self.conn.commit()
        return True

def run_rules_engine():
    """Run the rules engine to evaluate all transactions"""
    engine = RulesEngine()
    engine.connect_db()
    engine.load_rules()
    
    # Evaluate transactions against rules
    engine.evaluate_all_transactions()
    
    # Print results
    rule_counts = engine.get_rule_counts()
    print("\nRule Alert Counts:")
    for rule in rule_counts:
        print(f"{rule['name']}: {rule['alert_count']} alerts")
        
    # Get high risk transactions
    high_risk = engine.get_high_risk_transactions(threshold=0.7, limit=10)
    print(f"\nFound {len(high_risk)} high-risk transactions (score >= 0.7):")
    for tx in high_risk[:5]:  # Show top 5
        print(f"Transaction {tx['transaction_id']}: Risk Score {tx['final_risk_score']:.2f}, " +
              f"Amount: ${tx['amount']}, Country: {tx['country']}")
    
    engine.close_db()
    return engine

if __name__ == "__main__":
    run_rules_engine() 