import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_header():
    """Create dashboard header with title and info"""
    header = dbc.Row(
        [
            dbc.Col(
                html.H1("Fraud Detection System", className="text-primary"),
                width=8
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.P("Analyst Dashboard", className="lead"),
                            html.P(id="last-updated-time", className="text-muted small")
                        ],
                        className="text-right"
                    )
                ],
                width=4
            )
        ],
        className="mb-4 mt-3"
    )
    
    return header

def create_summary_cards(summary_data):
    """Create summary cards with key metrics"""
    cards = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(f"{summary_data['total_transactions']:,}", className="card-title text-center"),
                                html.P("Total Transactions", className="card-text text-center text-muted")
                            ]
                        )
                    ],
                    className="mb-4 shadow-sm"
                ),
                width=3
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(
                                    [
                                        f"{summary_data['fraud_transactions']:,} ",
                                        html.Small(f"({summary_data['fraud_percentage']:.2f}%)", className="text-muted")
                                    ], 
                                    className="card-title text-center text-danger"
                                ),
                                html.P("Fraud Transactions", className="card-text text-center text-muted")
                            ]
                        )
                    ],
                    className="mb-4 shadow-sm"
                ),
                width=3
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(
                                    [
                                        f"{summary_data['high_risk_transactions']:,} ",
                                        html.Small(f"({summary_data['high_risk_percentage']:.2f}%)", className="text-muted")
                                    ], 
                                    className="card-title text-center text-warning"
                                ),
                                html.P("High Risk Transactions", className="card-text text-center text-muted")
                            ]
                        )
                    ],
                    className="mb-4 shadow-sm"
                ),
                width=3
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H4(f"${summary_data['average_amount']:.2f}", className="card-title text-center"),
                                html.P("Average Transaction Amount", className="card-text text-center text-muted")
                            ]
                        )
                    ],
                    className="mb-4 shadow-sm"
                ),
                width=3
            )
        ]
    )
    
    alerts_card = dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Total Alerts"),
                    dbc.CardBody(
                        [
                            html.H3(f"{summary_data['total_alerts']:,}", className="card-title text-center text-info")
                        ]
                    )
                ],
                className="mb-4 shadow-sm"
            ),
        )
    )
    
    return dbc.Container([cards, alerts_card])

def create_tabs():
    """Create dashboard tabs"""
    tabs = dbc.Tabs(
        [
            dbc.Tab(label="Overview", tab_id="tab-overview"),
            dbc.Tab(label="Transactions", tab_id="tab-transactions"),
            dbc.Tab(label="Alerts", tab_id="tab-alerts"),
            dbc.Tab(label="Rules", tab_id="tab-rules"),
            dbc.Tab(label="Analytics", tab_id="tab-analytics"),
        ],
        id="dashboard-tabs",
        active_tab="tab-overview"
    )
    
    return tabs

def create_overview_tab():
    """Create overview tab content"""
    tab_content = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader("Fraud Trends"),
                            dbc.CardBody(
                                dcc.Graph(id="fraud-trend-chart", config={"displayModeBar": False})
                            )
                        ],
                        className="mb-4 shadow-sm"
                    )
                ],
                width=12
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader("Risk Score Distribution"),
                            dbc.CardBody(
                                dcc.Graph(id="risk-distribution-chart", config={"displayModeBar": False})
                            )
                        ],
                        className="mb-4 shadow-sm"
                    )
                ],
                lg=6
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader("Rule Performance"),
                            dbc.CardBody(
                                dcc.Graph(id="rule-performance-chart", config={"displayModeBar": False})
                            )
                        ],
                        className="mb-4 shadow-sm"
                    )
                ],
                lg=6
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader("Fraud by Country"),
                            dbc.CardBody(
                                dcc.Graph(id="country-risk-map", config={"displayModeBar": False})
                            )
                        ],
                        className="mb-4 shadow-sm"
                    )
                ],
                width=12
            )
        ]
    )
    
    return tab_content

def create_transactions_tab():
    """Create transactions tab content"""
    # Search filters
    filters = dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Transaction ID"),
                    dbc.Input(id="transaction-id-input", type="text", placeholder="Enter transaction ID...")
                ],
                lg=3
            ),
            dbc.Col(
                [
                    html.Label("User ID"),
                    dbc.Input(id="user-id-input", type="text", placeholder="Enter user ID...")
                ],
                lg=3
            ),
            dbc.Col(
                [
                    html.Label("Risk Score"),
                    dcc.RangeSlider(
                        id="risk-score-slider",
                        min=0,
                        max=1,
                        step=0.1,
                        value=[0.7, 1.0],
                        marks={i/10: str(i/10) for i in range(11)},
                        className="mt-3"
                    )
                ],
                lg=3
            ),
            dbc.Col(
                [
                    html.Label("Include Reviewed"),
                    dbc.Checklist(
                        options=[{"label": "Include", "value": 1}],
                        value=[],
                        id="include-reviewed-checkbox",
                        switch=True,
                        className="mt-3"
                    )
                ],
                lg=3
            ),
            dbc.Col(
                [
                    dbc.Button("Search", id="search-transactions-button", color="primary", className="mt-4 w-100")
                ],
                width=12
            )
        ],
        className="mb-4"
    )
    
    # Transactions table
    transactions_table = dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("High Risk Transactions"),
                    dbc.CardBody(
                        [
                            html.Div(id="transactions-table-container")
                        ]
                    )
                ],
                className="shadow-sm"
            )
        )
    )
    
    # Transaction details
    transaction_details = dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Transaction Details"),
                    dbc.CardBody(
                        [
                            html.Div(id="transaction-details-container", 
                                     children=[
                                         html.P("Select a transaction to see details.", className="text-muted")
                                     ])
                        ]
                    )
                ],
                className="shadow-sm mt-4"
            )
        )
    )
    
    tab_content = html.Div([filters, transactions_table, transaction_details])
    
    return tab_content

def create_alerts_tab():
    """Create alerts tab content"""
    # Alert filters
    filters = dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Status"),
                    dbc.Select(
                        id="alert-status-dropdown",
                        options=[
                            {"label": "All", "value": "all"},
                            {"label": "Open", "value": "open"},
                            {"label": "Closed", "value": "closed"},
                            {"label": "In Progress", "value": "in_progress"}
                        ],
                        value="open"
                    )
                ],
                lg=3
            ),
            dbc.Col(
                [
                    html.Label("Rule"),
                    dbc.Select(
                        id="alert-rule-dropdown",
                        options=[{"label": "All", "value": "all"}],  # Will be populated dynamically
                    )
                ],
                lg=3
            ),
            dbc.Col(
                [
                    html.Label("Min Risk Score"),
                    dcc.Slider(
                        id="alert-risk-slider",
                        min=0,
                        max=1,
                        step=0.1,
                        value=0.5,
                        marks={i/10: str(i/10) for i in range(11)},
                        className="mt-3"
                    )
                ],
                lg=3
            ),
            dbc.Col(
                [
                    dbc.Button("Search", id="search-alerts-button", color="primary", className="mt-4 w-100")
                ],
                lg=3
            )
        ],
        className="mb-4"
    )
    
    # Alerts table
    alerts_table = dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Alerts"),
                    dbc.CardBody(
                        [
                            html.Div(id="alerts-table-container")
                        ]
                    )
                ],
                className="shadow-sm"
            )
        )
    )
    
    # Alert details
    alert_details = dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Alert Details"),
                    dbc.CardBody(
                        [
                            html.Div(id="alert-details-container", 
                                     children=[
                                         html.P("Select an alert to see details.", className="text-muted")
                                     ])
                        ]
                    )
                ],
                className="shadow-sm mt-4"
            )
        )
    )
    
    tab_content = html.Div([filters, alerts_table, alert_details])
    
    return tab_content

def create_rules_tab():
    """Create rules tab content"""
    # Rules management
    rules_management = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Rules Management"),
                        dbc.CardBody(
                            [
                                html.P("Manage fraud detection rules"),
                                html.Div(id="rules-table-container")
                            ]
                        ),
                        dbc.CardFooter(
                            [
                                dbc.Button("Add New Rule", id="add-rule-button", color="success")
                            ]
                        )
                    ],
                    className="shadow-sm"
                )
            )
        ]
    )
    
    # Rule editor
    rule_editor = dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Rule Editor"),
                    dbc.CardBody(
                        [
                            html.Div(id="rule-editor-container", 
                                     children=[
                                         html.P("Select a rule to edit or click 'Add New Rule'.", className="text-muted")
                                     ])
                        ]
                    )
                ],
                className="shadow-sm mt-4"
            )
        )
    )
    
    tab_content = html.Div([rules_management, rule_editor])
    
    return tab_content

def create_analytics_tab():
    """Create analytics tab content"""
    tab_content = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader("Fraud Analysis"),
                            dbc.CardBody(
                                [
                                    html.Label("Analysis Type"),
                                    dbc.Select(
                                        id="analysis-type-dropdown",
                                        options=[
                                            {"label": "By Country", "value": "country"},
                                            {"label": "By Merchant Category", "value": "merchant_category"},
                                            {"label": "By Amount Range", "value": "amount"},
                                            {"label": "By Time Period", "value": "time"}
                                        ],
                                        value="country"
                                    ),
                                    html.Div(id="analysis-controls-container", className="mt-3"),
                                    dbc.Button("Run Analysis", id="run-analysis-button", color="primary", className="mt-3")
                                ]
                            )
                        ],
                        className="shadow-sm mb-4"
                    )
                ],
                lg=4
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader("Analysis Results"),
                            dbc.CardBody(
                                [
                                    html.Div(id="analysis-results-container", 
                                             children=[
                                                 html.P("Select analysis parameters and click 'Run Analysis'.", className="text-muted")
                                             ])
                                ]
                            )
                        ],
                        className="shadow-sm"
                    )
                ],
                lg=8
            )
        ]
    )
    
    return tab_content

def display_transaction_details(transaction_details):
    """Create a component to display transaction details"""
    if not transaction_details:
        return html.P("Transaction not found.", className="text-danger")
    
    # Main transaction information
    transaction_info = dbc.Row(
        [
            dbc.Col(
                [
                    html.H5("Transaction Information"),
                    dbc.Table(
                        [
                            html.Tbody([
                                html.Tr([html.Td("Transaction ID"), html.Td(transaction_details["transaction_id"])]),
                                html.Tr([html.Td("User ID"), html.Td(transaction_details["user_id"])]),
                                html.Tr([html.Td("Timestamp"), html.Td(transaction_details["timestamp"])]),
                                html.Tr([html.Td("Amount"), html.Td(f"${transaction_details['amount']:.2f}")]),
                                html.Tr([html.Td("Merchant Category"), html.Td(transaction_details["merchant_category"])]),
                                html.Tr([html.Td("Country"), html.Td(transaction_details["country"])]),
                                html.Tr([html.Td("Device ID"), html.Td(transaction_details["device_id"])]),
                                html.Tr([html.Td("IP Address"), html.Td(transaction_details["ip_address"])]),
                                html.Tr([
                                    html.Td("Is Fraud"), 
                                    html.Td(
                                        html.Span("Yes", className="badge bg-danger") if transaction_details["is_fraud"] 
                                        else html.Span("No", className="badge bg-success")
                                    )
                                ])
                            ])
                        ],
                        bordered=True,
                        size="sm",
                        className="mt-2"
                    )
                ],
                md=6
            ),
            dbc.Col(
                [
                    html.H5("Risk Assessment"),
                    dbc.Table(
                        [
                            html.Tbody([
                                html.Tr([
                                    html.Td("ML Score"), 
                                    html.Td(
                                        html.Div([
                                            html.Span(f"{transaction_details['ml_score']:.3f}" if transaction_details['ml_score'] is not None else "N/A"),
                                            dbc.Progress(
                                                value=transaction_details['ml_score']*100 if transaction_details['ml_score'] is not None else 0, 
                                                color="danger" if (transaction_details['ml_score'] or 0) > 0.7 else "warning" if (transaction_details['ml_score'] or 0) > 0.4 else "success",
                                                className="mt-1"
                                            )
                                        ])
                                    )
                                ]),
                                html.Tr([
                                    html.Td("Rule Score"), 
                                    html.Td(
                                        html.Div([
                                            html.Span(f"{transaction_details['rule_score']:.3f}" if transaction_details['rule_score'] is not None else "N/A"),
                                            dbc.Progress(
                                                value=transaction_details['rule_score']*100 if transaction_details['rule_score'] is not None else 0, 
                                                color="danger" if (transaction_details['rule_score'] or 0) > 0.7 else "warning" if (transaction_details['rule_score'] or 0) > 0.4 else "success",
                                                className="mt-1"
                                            )
                                        ])
                                    )
                                ]),
                                html.Tr([
                                    html.Td("Final Risk Score"), 
                                    html.Td(
                                        html.Div([
                                            html.Span(f"{transaction_details['final_risk_score']:.3f}" if transaction_details['final_risk_score'] is not None else "N/A"),
                                            dbc.Progress(
                                                value=transaction_details['final_risk_score']*100 if transaction_details['final_risk_score'] is not None else 0, 
                                                color="danger" if (transaction_details['final_risk_score'] or 0) > 0.7 else "warning" if (transaction_details['final_risk_score'] or 0) > 0.4 else "success",
                                                className="mt-1"
                                            )
                                        ])
                                    )
                                ])
                            ])
                        ],
                        bordered=True,
                        size="sm",
                        className="mt-2"
                    ),
                    html.H5("User Information", className="mt-3"),
                    dbc.Table(
                        [
                            html.Tbody([
                                html.Tr([html.Td("Account Age"), html.Td(f"{transaction_details['account_age_days']} days")]),
                                html.Tr([html.Td("Country of Residence"), html.Td(transaction_details["country_of_residence"])]),
                                html.Tr([
                                    html.Td("Country Match"), 
                                    html.Td(
                                        html.Span("Yes", className="badge bg-success") if transaction_details["country"] == transaction_details["country_of_residence"]
                                        else html.Span("No", className="badge bg-danger")
                                    )
                                ]),
                                html.Tr([html.Td("Account Type"), html.Td(transaction_details["account_type"].title())]),
                                html.Tr([
                                    html.Td("Verified Email"), 
                                    html.Td(
                                        html.Span("Yes", className="badge bg-success") if transaction_details["has_verified_email"]
                                        else html.Span("No", className="badge bg-danger")
                                    )
                                ]),
                                html.Tr([
                                    html.Td("Verified Phone"), 
                                    html.Td(
                                        html.Span("Yes", className="badge bg-success") if transaction_details["has_verified_phone"]
                                        else html.Span("No", className="badge bg-danger")
                                    )
                                ]),
                            ])
                        ],
                        bordered=True,
                        size="sm",
                        className="mt-2"
                    )
                ],
                md=6
            )
        ]
    )
    
    # Alerts
    alerts = transaction_details.get('alerts', [])
    alerts_section = html.Div(
        [
            html.H5(f"Alerts ({len(alerts)})", className="mt-3"),
            dbc.Table(
                [
                    html.Thead([
                        html.Tr([
                            html.Th("Rule"),
                            html.Th("Description"),
                            html.Th("Risk Score"),
                            html.Th("Status"),
                            html.Th("Actions")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(alert["rule_name"]),
                            html.Td(alert["description"]),
                            html.Td(f"{alert['risk_score']:.2f}"),
                            html.Td(
                                html.Span(alert["status"].title(), className=f"badge bg-{'success' if alert['status']=='closed' else 'warning' if alert['status']=='in_progress' else 'danger'}")
                            ),
                            html.Td(
                                dbc.ButtonGroup([
                                    dbc.Button("Approve", color="success", size="sm", className="me-1"),
                                    dbc.Button("Reject", color="danger", size="sm")
                                ])
                            )
                        ]) for alert in alerts
                    ]) if alerts else html.Tbody([html.Tr([html.Td("No alerts for this transaction.", colSpan=5)])])
                ],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True,
                size="sm",
                className="mt-2"
            )
        ]
    ) if alerts else html.Div()
    
    # User transaction history
    history = transaction_details.get('user_history', [])
    history_section = html.Div(
        [
            html.H5(f"User Transaction History ({len(history)})", className="mt-3"),
            dbc.Table(
                [
                    html.Thead([
                        html.Tr([
                            html.Th("Transaction ID"),
                            html.Th("Timestamp"),
                            html.Th("Amount"),
                            html.Th("Merchant Category"),
                            html.Th("Country"),
                            html.Th("Risk Score"),
                            html.Th("Fraud")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(
                                dbc.Button(
                                    tx["transaction_id"], 
                                    color="link", 
                                    id={"type": "tx-history-link", "index": tx["transaction_id"]},
                                    className="p-0"
                                )
                            ),
                            html.Td(tx["timestamp"]),
                            html.Td(f"${tx['amount']:.2f}"),
                            html.Td(tx["merchant_category"]),
                            html.Td(tx["country"]),
                            html.Td(f"{tx['final_risk_score']:.3f}" if tx['final_risk_score'] is not None else "N/A"),
                            html.Td(
                                html.Span("Yes", className="badge bg-danger") if tx["is_fraud"]
                                else html.Span("No", className="badge bg-success")
                            ),
                        ]) for tx in history
                    ])
                ],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True,
                size="sm",
                className="mt-2"
            )
        ]
    ) if history else html.Div()
    
    # Review section
    review_section = html.Div(
        [
            html.H5("Transaction Review", className="mt-3"),
            dbc.Textarea(
                id="transaction-review-notes",
                placeholder="Enter review notes here...",
                value=transaction_details.get("review_notes", ""),
                style={"height": "100px"},
                className="mb-2"
            ),
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Mark as Reviewed",
                        id={"type": "mark-reviewed-button", "index": transaction_details["transaction_id"]},
                        color="primary",
                        className="w-100"
                    )
                ], md=6),
                dbc.Col([
                    dbc.Button(
                        "Flag as Fraud",
                        id={"type": "flag-fraud-button", "index": transaction_details["transaction_id"]},
                        color="danger",
                        className="w-100"
                    )
                ], md=6)
            ])
        ]
    )
    
    return html.Div([transaction_info, alerts_section, history_section, review_section]) 