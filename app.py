import dash
from dash import html, dcc, dash_table, callback
from dash.dependencies import Input, Output, State, ClientsideFunction, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import modules
from utils.data_utils import (
    get_transaction_summary, get_transaction_details, 
    create_fraud_trend_chart, create_risk_distribution_chart,
    create_rule_performance_chart, create_country_risk_map,
    execute_query
)
from dashboard.layouts import (
    create_header, create_summary_cards, create_tabs,
    create_overview_tab, create_transactions_tab, 
    create_alerts_tab, create_rules_tab, create_analytics_tab,
    display_transaction_details
)
from models.fraud_detector import FraudDetector
from rules.rules_engine import RulesEngine

# Initialize the Dash app
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
server = app.server

# Initialize models and engines
fraud_detector = FraudDetector()
rules_engine = RulesEngine()

# App layout
def serve_layout():
    """Create dynamic layout with latest data"""
    # Get transaction summary for cards
    summary_data = get_transaction_summary()
    
    return dbc.Container(
        [
            # Header
            create_header(),
            
            # Summary cards
            create_summary_cards(summary_data),
            
            # Tabs
            create_tabs(),
            
            # Tab content
            html.Div(id="tab-content", className="p-4"),
            
            # Store component for current transaction
            dcc.Store(id="current-transaction-id"),
            
            # Store component for current alert
            dcc.Store(id="current-alert-id"),
            
            # Store component for current rule
            dcc.Store(id="current-rule-id"),
            
            # Interval for auto-refresh
            dcc.Interval(
                id="interval-component",
                interval=300*1000,  # 5 minutes in milliseconds
                n_intervals=0
            )
        ],
        fluid=True,
        className="mt-4"
    )

app.layout = serve_layout

# Callbacks

@app.callback(
    Output("last-updated-time", "children"),
    Input("interval-component", "n_intervals")
)
def update_time(n):
    """Update the last updated time"""
    return f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@app.callback(
    Output("tab-content", "children"),
    Input("dashboard-tabs", "active_tab")
)
def render_tab_content(active_tab):
    """Render content based on active tab"""
    if active_tab == "tab-overview":
        return create_overview_tab()
    elif active_tab == "tab-transactions":
        return create_transactions_tab()
    elif active_tab == "tab-alerts":
        return create_alerts_tab()
    elif active_tab == "tab-rules":
        return create_rules_tab()
    elif active_tab == "tab-analytics":
        return create_analytics_tab()
    else:
        return html.P("Tab content not found.")

@app.callback(
    [Output("fraud-trend-chart", "figure"),
     Output("risk-distribution-chart", "figure"),
     Output("rule-performance-chart", "figure"),
     Output("country-risk-map", "figure")],
    Input("interval-component", "n_intervals")
)
def update_charts(n):
    """Update all charts on the overview tab"""
    fraud_trend = create_fraud_trend_chart()
    risk_dist = create_risk_distribution_chart()
    rule_perf = create_rule_performance_chart()
    country_map = create_country_risk_map()
    
    return fraud_trend, risk_dist, rule_perf, country_map

@app.callback(
    Output("transactions-table-container", "children"),
    [Input("search-transactions-button", "n_clicks"),
     Input("interval-component", "n_intervals")],
    [State("transaction-id-input", "value"),
     State("user-id-input", "value"),
     State("risk-score-slider", "value"),
     State("include-reviewed-checkbox", "value")]
)
def update_transactions_table(n_clicks, n_intervals, transaction_id, user_id, risk_range, include_reviewed):
    """Update transactions table based on filters"""
    # Start with base query
    query = """
    SELECT t.transaction_id, t.user_id, t.timestamp, t.amount, 
           t.merchant_category, t.country, t.final_risk_score,
           t.is_fraud, t.reviewed
    FROM transactions t
    WHERE 1=1
    """
    
    params = {}
    
    # Apply filters
    if transaction_id:
        query += " AND t.transaction_id LIKE :transaction_id"
        params['transaction_id'] = f"%{transaction_id}%"
    
    if user_id:
        query += " AND t.user_id LIKE :user_id"
        params['user_id'] = f"%{user_id}%"
    
    if risk_range:
        query += " AND (t.final_risk_score >= :min_risk AND t.final_risk_score <= :max_risk)"
        params['min_risk'] = risk_range[0]
        params['max_risk'] = risk_range[1]
    
    if not include_reviewed or 1 not in include_reviewed:
        query += " AND t.reviewed = 0"
    
    # Order by risk score
    query += " ORDER BY t.final_risk_score DESC, t.timestamp DESC LIMIT 100"
    
    # Execute query
    df = execute_query(query, params)
    
    # Create formatted columns
    df['amount'] = df['amount'].apply(lambda x: f"${x:.2f}")
    df['final_risk_score'] = df['final_risk_score'].apply(lambda x: f"{x:.3f}" if x is not None else "N/A")
    df['is_fraud'] = df['is_fraud'].apply(lambda x: "Yes" if x else "No")
    df['reviewed'] = df['reviewed'].apply(lambda x: "Yes" if x else "No")
    
    # Create DataTable
    table = dash_table.DataTable(
        id="transactions-table",
        columns=[
            {"name": "Transaction ID", "id": "transaction_id"},
            {"name": "User ID", "id": "user_id"},
            {"name": "Timestamp", "id": "timestamp"},
            {"name": "Amount", "id": "amount"},
            {"name": "Merchant Category", "id": "merchant_category"},
            {"name": "Country", "id": "country"},
            {"name": "Risk Score", "id": "final_risk_score"},
            {"name": "Fraud", "id": "is_fraud"},
            {"name": "Reviewed", "id": "reviewed"},
        ],
        data=df.to_dict("records"),
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "5px",
            "minWidth": "80px",
        },
        style_header={
            "backgroundColor": "#f8f9fa",
            "fontWeight": "bold"
        },
        style_data_conditional=[
            {
                "if": {"filter_query": "{is_fraud} = 'Yes'"},
                "backgroundColor": "#ffebee",
            },
            {
                "if": {"filter_query": "{reviewed} = 'Yes'"},
                "backgroundColor": "#e8f5e9",
            }
        ],
        row_selectable="single",
        selected_rows=[],
    )
    
    return table

@app.callback(
    Output("current-transaction-id", "data"),
    Input("transactions-table", "selected_rows"),
    State("transactions-table", "data"),
    prevent_initial_call=True
)
def store_selected_transaction(selected_rows, data):
    """Store selected transaction ID"""
    if selected_rows and data:
        return data[selected_rows[0]]["transaction_id"]
    return None

@app.callback(
    Output("transaction-details-container", "children"),
    Input("current-transaction-id", "data"),
    prevent_initial_call=True
)
def display_selected_transaction(transaction_id):
    """Display details for selected transaction"""
    if transaction_id:
        details = get_transaction_details(transaction_id)
        return display_transaction_details(details)
    return html.P("Select a transaction to see details.", className="text-muted")

@app.callback(
    Output("alerts-table-container", "children"),
    [Input("search-alerts-button", "n_clicks"),
     Input("interval-component", "n_intervals")],
    [State("alert-status-dropdown", "value"),
     State("alert-rule-dropdown", "value"),
     State("alert-risk-slider", "value")]
)
def update_alerts_table(n_clicks, n_intervals, status, rule_id, min_risk):
    """Update alerts table based on filters"""
    # Start with base query
    query = """
    SELECT a.alert_id, a.transaction_id, r.name as rule_name, 
           a.risk_score, a.created_at, a.status,
           t.amount, t.merchant_category, t.country, t.is_fraud
    FROM alerts a
    JOIN rules r ON a.rule_id = r.rule_id
    JOIN transactions t ON a.transaction_id = t.transaction_id
    WHERE 1=1
    """
    
    params = {}
    
    # Apply filters
    if status and status != "all":
        query += " AND a.status = :status"
        params['status'] = status
    
    if rule_id and rule_id != "all":
        query += " AND a.rule_id = :rule_id"
        params['rule_id'] = rule_id
    
    if min_risk:
        query += " AND a.risk_score >= :min_risk"
        params['min_risk'] = min_risk
    
    # Order by risk score
    query += " ORDER BY a.risk_score DESC, a.created_at DESC LIMIT 100"
    
    # Execute query
    df = execute_query(query, params)
    
    # Create formatted columns
    df['amount'] = df['amount'].apply(lambda x: f"${x:.2f}")
    df['risk_score'] = df['risk_score'].apply(lambda x: f"{x:.3f}" if x is not None else "N/A")
    df['is_fraud'] = df['is_fraud'].apply(lambda x: "Yes" if x else "No")
    
    # Create DataTable
    table = dash_table.DataTable(
        id="alerts-table",
        columns=[
            {"name": "Alert ID", "id": "alert_id"},
            {"name": "Transaction ID", "id": "transaction_id"},
            {"name": "Rule", "id": "rule_name"},
            {"name": "Risk Score", "id": "risk_score"},
            {"name": "Created At", "id": "created_at"},
            {"name": "Status", "id": "status"},
            {"name": "Amount", "id": "amount"},
            {"name": "Merchant Category", "id": "merchant_category"},
            {"name": "Country", "id": "country"},
            {"name": "Fraud", "id": "is_fraud"},
        ],
        data=df.to_dict("records"),
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "5px",
            "minWidth": "80px",
        },
        style_header={
            "backgroundColor": "#f8f9fa",
            "fontWeight": "bold"
        },
        style_data_conditional=[
            {
                "if": {"filter_query": "{status} = 'open'"},
                "backgroundColor": "#ffebee",
            },
            {
                "if": {"filter_query": "{status} = 'closed'"},
                "backgroundColor": "#e8f5e9",
            },
            {
                "if": {"filter_query": "{status} = 'in_progress'"},
                "backgroundColor": "#fff8e1",
            },
            {
                "if": {"filter_query": "{is_fraud} = 'Yes'"},
                "backgroundColor": "#ffcdd2",
            }
        ],
        row_selectable="single",
        selected_rows=[],
    )
    
    return table

# Run the app
if __name__ == "__main__":
    # Generate data if needed
    if not os.path.exists("db/fraud_detection.db"):
        print("Database not found. Running setup scripts...")
        
        # Run setup scripts
        import subprocess
        subprocess.run(["python", "scripts/setup_database.py"], check=True)
        
        # Train model
        from models.fraud_detector import train_model
        train_model()
        
        # Run rules engine
        from rules.rules_engine import run_rules_engine
        run_rules_engine()
    
    # Run app
    app.run_server(debug=True, port=8050)