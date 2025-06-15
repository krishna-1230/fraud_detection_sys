import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random

def generate_transaction_data(num_users=1000, num_transactions=10000, fraud_percentage=0.05):
    """
    Generate synthetic transaction data with fraud patterns
    
    Parameters:
    num_users: Number of unique users
    num_transactions: Number of transactions to generate
    fraud_percentage: Percentage of transactions that are fraudulent
    """
    # Create user data
    user_ids = [f"U{i:06d}" for i in range(1, num_users + 1)]
    
    # User profiles for more realistic patterns
    user_profiles = {
        user_id: {
            "age": random.randint(18, 80),
            "typical_amount": random.uniform(10, 500),
            "amount_std": random.uniform(5, 100),
            "typical_merchant_categories": random.sample(
                ["grocery", "restaurant", "retail", "electronics", "travel", 
                 "gas", "utilities", "healthcare", "entertainment", "subscription"], 
                random.randint(3, 6)
            ),
            "country": random.choice(["US", "CA", "UK", "FR", "DE", "AU", "JP"])
        } for user_id in user_ids
    }
    
    # Create timestamp range (last 90 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Generate transaction data
    transactions = []
    
    # Normal transactions
    num_normal = int(num_transactions * (1 - fraud_percentage))
    normal_user_ids = np.random.choice(user_ids, num_normal)
    
    for i in range(num_normal):
        user_id = normal_user_ids[i]
        profile = user_profiles[user_id]
        
        # Generate timestamp
        timestamp = start_date + (end_date - start_date) * random.random()
        
        # Generate merchant category
        merchant_category = random.choice(profile["typical_merchant_categories"])
        
        # Generate amount based on user profile
        amount = max(0.01, np.random.normal(
            profile["typical_amount"], 
            profile["amount_std"]
        ))
        
        # Generate location consistent with user
        country = profile["country"]
        
        # Device and IP info
        device_id = f"DEV{user_id[1:]}"
        ip_address = f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        # Normal transactions
        transactions.append({
            "transaction_id": f"T{i:08d}",
            "user_id": user_id,
            "timestamp": timestamp,
            "amount": round(amount, 2),
            "merchant_category": merchant_category,
            "country": country,
            "device_id": device_id,
            "ip_address": ip_address,
            "is_fraud": 0
        })
    
    # Fraudulent transactions
    num_fraud = int(num_transactions * fraud_percentage)
    
    # Different fraud patterns
    fraud_patterns = [
        "unusual_amount",
        "unusual_location",
        "unusual_merchant",
        "unusual_device",
        "unusual_frequency"
    ]
    
    for i in range(num_fraud):
        # Select random user
        user_id = random.choice(user_ids)
        profile = user_profiles[user_id]
        
        # Generate timestamp
        timestamp = start_date + (end_date - start_date) * random.random()
        
        # Select fraud pattern
        pattern = random.choice(fraud_patterns)
        
        if pattern == "unusual_amount":
            # Much higher amount than usual
            amount = profile["typical_amount"] * random.uniform(5, 20)
            merchant_category = random.choice(profile["typical_merchant_categories"])
            country = profile["country"]
            device_id = f"DEV{user_id[1:]}"
            
        elif pattern == "unusual_location":
            # Transaction from unusual country
            amount = random.uniform(50, 5000)
            merchant_category = random.choice([
                "travel", "hotel", "casino", "jewelry", "atm_withdrawal"
            ])
            countries = ["RU", "NG", "BR", "CN", "ID", "UA"]
            country = random.choice([c for c in countries if c != profile["country"]])
            device_id = f"DEV{user_id[1:]}"
            
        elif pattern == "unusual_merchant":
            # Unusual merchant category
            amount = random.uniform(100, 2000)
            merchant_category = random.choice([
                "gambling", "crypto", "money_transfer", "jewelry", "electronics"
            ])
            country = profile["country"]
            device_id = f"DEV{user_id[1:]}"
            
        elif pattern == "unusual_device":
            # New device
            amount = random.uniform(50, 500)
            merchant_category = random.choice([
                "electronics", "subscription", "gaming", "digital_goods"
            ])
            country = profile["country"]
            device_id = f"NEW{random.randint(10000, 99999)}"
            
        else:  # unusual_frequency
            # Multiple transactions in short time
            amount = random.uniform(10, 200)
            merchant_category = random.choice([
                "retail", "restaurant", "gas", "atm_withdrawal"
            ])
            country = profile["country"]
            device_id = f"DEV{user_id[1:]}"
        
        # IP address - for fraud sometimes different
        if random.random() < 0.7:  # 70% chance of suspicious IP
            ip_address = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        else:
            ip_address = f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        transactions.append({
            "transaction_id": f"T{num_normal+i:08d}",
            "user_id": user_id,
            "timestamp": timestamp,
            "amount": round(amount, 2),
            "merchant_category": merchant_category,
            "country": country,
            "device_id": device_id,
            "ip_address": ip_address,
            "is_fraud": 1
        })
    
    # Convert to dataframe and sort by timestamp
    df = pd.DataFrame(transactions)
    df = df.sort_values("timestamp")
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    return df

def generate_user_data(transaction_df):
    """Generate user profile data based on transactions"""
    user_ids = transaction_df["user_id"].unique()
    
    users = []
    for user_id in user_ids:
        user_transactions = transaction_df[transaction_df["user_id"] == user_id]
        
        # Get the most common country
        if len(user_transactions) > 0:
            most_common_country = user_transactions["country"].mode()[0]
        else:
            most_common_country = "US"
        
        users.append({
            "user_id": user_id,
            "account_age_days": random.randint(30, 3650),  # 1 month to 10 years
            "country_of_residence": most_common_country,
            "num_payment_methods": random.randint(1, 5),
            "account_type": random.choice(["standard", "premium", "business"]),
            "has_verified_email": random.random() < 0.95,  # 95% have verified email
            "has_verified_phone": random.random() < 0.85,  # 85% have verified phone
            "risk_score": round(random.uniform(0, 100), 2)
        })
    
    return pd.DataFrame(users)

def generate_merchant_data(transaction_df):
    """Generate merchant data based on transactions"""
    # Get unique combinations of merchant category and country
    merchant_combos = transaction_df[["merchant_category", "country"]].drop_duplicates().reset_index(drop=True)
    
    merchants = []
    for idx, row in merchant_combos.iterrows():
        merchant_id = f"M{idx:06d}"
        
        merchants.append({
            "merchant_id": merchant_id,
            "merchant_name": f"{row['merchant_category'].title()} {random.choice(['Store', 'Shop', 'Mart', 'Market', 'Place'])}{random.randint(1, 999)}",
            "merchant_category": row["merchant_category"],
            "country": row["country"],
            "average_transaction_amount": round(random.uniform(10, 500), 2),
            "merchant_risk_score": round(random.uniform(0, 100), 2)
        })
    
    return pd.DataFrame(merchants)

def main():
    print("Generating synthetic transaction data...")
    transaction_data = generate_transaction_data(num_users=1000, num_transactions=10000)
    
    print("Generating user profiles...")
    user_data = generate_user_data(transaction_data)
    
    print("Generating merchant data...")
    merchant_data = generate_merchant_data(transaction_data)
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Save to CSV files
    transaction_data.to_csv("data/transactions.csv", index=False)
    user_data.to_csv("data/users.csv", index=False)
    merchant_data.to_csv("data/merchants.csv", index=False)
    
    print(f"Generated {len(transaction_data)} transactions")
    print(f"Generated {len(user_data)} user profiles")
    print(f"Generated {len(merchant_data)} merchants")
    print("Data saved to 'data/' directory")

if __name__ == "__main__":
    main() 