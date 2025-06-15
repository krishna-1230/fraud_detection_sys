import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def connect_db():
    """Connect to SQLite database"""
    conn = sqlite3.connect("db/fraud_detection.db")
    return conn

def execute_query(query, params=None):
    """Execute SQL query and return results as pandas DataFrame"""
    conn = connect_db()
    
    if params:
        df = pd.read_sql_query(query, conn, params=params)
    else:
        df = pd.read_sql_query(query, conn)
        
    conn.close()
    return df

def get_transaction_details(transaction_id):
    """Get detailed information about a transaction"""
    query = """
    SELECT 
        t.transaction_id, t.user_id, t.timestamp, t.amount, 
        t.merchant_category, t.country, t.device_id, t.ip_address,
        t.is_fraud, t.ml_score, t.rule_score, t.final_risk_score, 
        t.reviewed, t.review_notes,
        u.account_age_days, u.country_of_residence, u.num_payment_methods,
        u.account_type, u.has_verified_email, u.has_verified_phone, u.risk_score
    FROM transactions t
    JOIN users u ON t.user_id = u.user_id
    WHERE t.transaction_id = ?
    """
    
    df = execute_query(query, (transaction_id,))
    
    if len(df) == 0:
        return None
    
    # Convert to dictionary
    details = df.iloc[0].to_dict()
    
    # Get user transaction history
    user_id = details['user_id']
    history_query = """
    SELECT transaction_id, timestamp, amount, merchant_category, 
           country, is_fraud, final_risk_score
    FROM transactions
    WHERE user_id = ?
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    history = execute_query(history_query, (user_id,))
    details['user_history'] = history.to_dict('records')
    
    # Get related alerts
    alerts_query = """
    SELECT a.alert_id, r.name as rule_name, r.description, a.created_at, 
           a.risk_score, a.status, a.resolution
    FROM alerts a
    JOIN rules r ON a.rule_id = r.rule_id
    WHERE a.transaction_id = ?
    ORDER BY a.risk_score DESC
    """
    
    alerts = execute_query(alerts_query, (transaction_id,))
    details['alerts'] = alerts.to_dict('records')
    
    return details

def get_transaction_summary():
    """Get summary statistics about transactions"""
    # Total transactions
    total_query = "SELECT COUNT(*) as total FROM transactions"
    total = execute_query(total_query).iloc[0]['total']
    
    # Fraud transactions
    fraud_query = "SELECT COUNT(*) as fraud FROM transactions WHERE is_fraud = 1"
    fraud = execute_query(fraud_query).iloc[0]['fraud']
    
    # High risk transactions
    high_risk_query = """
    SELECT COUNT(*) as high_risk 
    FROM transactions 
    WHERE final_risk_score >= 0.7 OR is_fraud = 1
    """
    high_risk = execute_query(high_risk_query).iloc[0]['high_risk']
    
    # Alerts
    alerts_query = "SELECT COUNT(*) as alerts FROM alerts"
    alerts = execute_query(alerts_query).iloc[0]['alerts']
    
    # Average transaction amount
    avg_amount_query = "SELECT AVG(amount) as avg_amount FROM transactions"
    avg_amount = execute_query(avg_amount_query).iloc[0]['avg_amount']
    
    # Top merchant categories
    merchant_query = """
    SELECT merchant_category, COUNT(*) as count
    FROM transactions
    GROUP BY merchant_category
    ORDER BY count DESC
    LIMIT 5
    """
    top_merchants = execute_query(merchant_query)
    
    # Top countries
    country_query = """
    SELECT country, COUNT(*) as count
    FROM transactions
    GROUP BY country
    ORDER BY count DESC
    LIMIT 5
    """
    top_countries = execute_query(country_query)
    
    return {
        'total_transactions': total,
        'fraud_transactions': fraud,
        'fraud_percentage': (fraud / total) * 100 if total > 0 else 0,
        'high_risk_transactions': high_risk,
        'high_risk_percentage': (high_risk / total) * 100 if total > 0 else 0,
        'total_alerts': alerts,
        'average_amount': avg_amount,
        'top_merchants': top_merchants.to_dict('records'),
        'top_countries': top_countries.to_dict('records')
    }

def get_user_summary(user_id):
    """Get summary information about a user"""
    # User details
    user_query = """
    SELECT * FROM users WHERE user_id = ?
    """
    user_details = execute_query(user_query, (user_id,))
    
    if len(user_details) == 0:
        return None
    
    # User transactions
    transactions_query = """
    SELECT COUNT(*) as total_transactions,
           SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_transactions,
           AVG(amount) as avg_amount,
           MAX(amount) as max_amount,
           MIN(amount) as min_amount,
           COUNT(DISTINCT country) as unique_countries,
           COUNT(DISTINCT merchant_category) as unique_merchant_categories
    FROM transactions
    WHERE user_id = ?
    """
    
    tx_summary = execute_query(transactions_query, (user_id,))
    
    # Combine results
    result = user_details.iloc[0].to_dict()
    result.update(tx_summary.iloc[0].to_dict())
    
    # Get transaction history
    history_query = """
    SELECT transaction_id, timestamp, amount, merchant_category, country, 
           is_fraud, final_risk_score
    FROM transactions
    WHERE user_id = ?
    ORDER BY timestamp DESC
    """
    
    history = execute_query(history_query, (user_id,))
    result['transaction_history'] = history.to_dict('records')
    
    return result

def create_fraud_trend_chart():
    """Create a chart showing fraud trends over time"""
    query = """
    SELECT 
        SUBSTR(timestamp, 1, 10) as date,
        COUNT(*) as total_transactions,
        SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_transactions,
        AVG(final_risk_score) as avg_risk_score
    FROM transactions
    GROUP BY SUBSTR(timestamp, 1, 10)
    ORDER BY date
    """
    
    df = execute_query(query)
    
    # Calculate fraud percentage
    df['fraud_percentage'] = (df['fraud_transactions'] / df['total_transactions']) * 100
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add traces
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['total_transactions'], 
                   name="Total Transactions", line=dict(color='blue')),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['fraud_transactions'], 
                   name="Fraud Transactions", line=dict(color='red')),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['fraud_percentage'], 
                   name="Fraud %", line=dict(color='orange', dash='dash')),
        secondary_y=True,
    )
    
    # Add figure title
    fig.update_layout(
        title_text="Transaction and Fraud Trends",
        height=500,
    )
    
    # Set x-axis title
    fig.update_xaxes(title_text="Date")
    
    # Set y-axes titles
    fig.update_yaxes(title_text="Number of Transactions", secondary_y=False)
    fig.update_yaxes(title_text="Fraud %", secondary_y=True)
    
    return fig

def create_risk_distribution_chart():
    """Create a histogram of risk scores"""
    query = """
    SELECT final_risk_score, is_fraud
    FROM transactions
    WHERE final_risk_score IS NOT NULL
    """
    
    df = execute_query(query)
    
    fig = px.histogram(
        df, 
        x="final_risk_score", 
        color="is_fraud",
        color_discrete_map={0: "blue", 1: "red"},
        labels={"final_risk_score": "Risk Score", "is_fraud": "Fraud"},
        title="Distribution of Risk Scores",
        barmode="overlay",
        opacity=0.7,
        nbins=20,
        height=400,
    )
    
    fig.update_layout(
        xaxis_title="Risk Score",
        yaxis_title="Number of Transactions",
        legend_title="Is Fraud",
    )
    
    return fig

def create_rule_performance_chart():
    """Create a chart showing rule performance"""
    query = """
    SELECT r.name, 
           COUNT(a.alert_id) as total_alerts,
           SUM(CASE WHEN t.is_fraud = 1 THEN 1 ELSE 0 END) as caught_fraud
    FROM rules r
    JOIN alerts a ON r.rule_id = a.rule_id
    JOIN transactions t ON a.transaction_id = t.transaction_id
    GROUP BY r.name
    ORDER BY caught_fraud DESC
    """
    
    df = execute_query(query)
    
    # Calculate precision
    df['precision'] = (df['caught_fraud'] / df['total_alerts']) * 100
    
    fig = px.bar(
        df,
        y="name",
        x="total_alerts",
        color="precision",
        orientation="h",
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={
            "name": "Rule Name",
            "total_alerts": "Number of Alerts",
            "precision": "Precision %"
        },
        title="Rule Performance",
        height=500,
    )
    
    fig.update_layout(
        xaxis_title="Number of Alerts",
        yaxis_title="Rule",
        coloraxis_colorbar_title="Precision %",
    )
    
    return fig

def create_country_risk_map():
    """Create a choropleth map of transaction risk by country"""
    query = """
    SELECT 
        country, 
        COUNT(*) as total_transactions,
        AVG(final_risk_score) as avg_risk_score,
        SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count
    FROM transactions
    GROUP BY country
    """
    
    df = execute_query(query)
    
    # Calculate fraud rate
    df['fraud_rate'] = (df['fraud_count'] / df['total_transactions']) * 100
    
    fig = px.choropleth(
        df,
        locations="country",
        color="fraud_rate",
        hover_name="country",
        hover_data=["total_transactions", "avg_risk_score", "fraud_count"],
        color_continuous_scale=px.colors.sequential.Plasma,
        labels={
            "fraud_rate": "Fraud Rate %",
            "avg_risk_score": "Avg Risk Score",
            "total_transactions": "Total Transactions",
            "fraud_count": "Fraud Transactions"
        },
        title="Fraud Rate by Country",
    )
    
    fig.update_layout(
        height=500,
        geo=dict(
            showframe=False,
            showcoastlines=True,
        )
    )
    
    return fig 