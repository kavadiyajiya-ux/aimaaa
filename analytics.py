import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from ticketing import load_tickets_df

# Enterprise Color Palette
COLOR_MAP_CATEGORY = {
    "IT": "#3A86C8",       # Soft Blue
    "HR": "#9B59B6",       # Soft Purple
    "Payroll": "#2ECC71",  # Soft Green
    "Security": "#E74C3C", # Soft Red
    "Operations": "#F39C12" # Soft Orange
}

COLOR_MAP_PRIORITY = {
    "Low": "#2ECC71",      # Green
    "Medium": "#3498DB",   # Blue
    "High": "#E67E22",     # Orange
    "Critical": "#E74C3C"  # Red
}

def apply_glass_theme(fig, title: str):
    """
    Applies consistent dark-mode glassmorphism styling to Plotly figures.
    """
    fig.update_layout(
        title={
            'text': title,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#E0E6ED',
        font_family='Inter, Outfit, sans-serif',
        title_font_color='#FFFFFF',
        title_font_size=18,
        legend={
            'bgcolor': 'rgba(20, 24, 33, 0.6)',
            'bordercolor': 'rgba(255, 255, 255, 0.1)',
            'borderwidth': 1
        },
        margin=dict(l=40, r=40, t=55, b=40)
    )
    # Style axes grids
    fig.update_xaxes(
        gridcolor='rgba(255, 255, 255, 0.05)',
        zerolinecolor='rgba(255, 255, 255, 0.1)',
        tickfont=dict(color='#A0AEC0')
    )
    fig.update_yaxes(
        gridcolor='rgba(255, 255, 255, 0.05)',
        zerolinecolor='rgba(255, 255, 255, 0.1)',
        tickfont=dict(color='#A0AEC0')
    )
    return fig

def get_category_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Pie chart showing incident volume across categories.
    """
    if df.empty:
        fig = px.pie(names=["No Data"], values=[1])
        return apply_glass_theme(fig, "Category Distribution")
        
    counts = df["category"].value_counts().rename_axis("Category").reset_index(name="Volume")
    
    fig = px.pie(
        counts, 
        names="Category", 
        values="Volume",
        color="Category",
        color_discrete_map=COLOR_MAP_CATEGORY,
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return apply_glass_theme(fig, "Category Distribution")

def get_priority_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Ordered bar chart demonstrating incidents per priority level.
    """
    if df.empty:
        fig = px.bar(x=["Low", "Medium", "High", "Critical"], y=[0, 0, 0, 0])
        return apply_glass_theme(fig, "Priority Distribution")
        
    # Standardize and count
    counts = df["priority"].value_counts().rename_axis("Priority").reset_index(name="Count")
    
    # Ensure all priorities are present in categories for ordering
    priority_order = ["Low", "Medium", "High", "Critical"]
    counts["Priority"] = pd.Categorical(counts["Priority"], categories=priority_order, ordered=True)
    counts = counts.sort_values("Priority")
    
    fig = px.bar(
        counts, 
        x="Priority", 
        y="Count",
        color="Priority",
        color_discrete_map=COLOR_MAP_PRIORITY
    )
    fig.update_layout(xaxis_title=None, yaxis_title="Number of Tickets", showlegend=False)
    return apply_glass_theme(fig, "Priority Distribution")

def get_escalation_rate_chart(df: pd.DataFrame) -> go.Figure:
    """
    Pie chart detailing standard support vs escalated tickets.
    """
    if df.empty:
        fig = px.pie(names=["No Data"], values=[1])
        return apply_glass_theme(fig, "Escalation Rate")
        
    counts = df["escalated"].value_counts().rename_axis("Status").reset_index(name="Count")
    counts["Status"] = counts["Status"].map({True: "Escalated", False: "Standard Support"})
    
    fig = px.pie(
        counts, 
        names="Status", 
        values="Count",
        color="Status",
        color_discrete_map={"Escalated": "#E74C3C", "Standard Support": "#3498DB"},
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return apply_glass_theme(fig, "Escalation Rate")

def get_daily_ticket_chart(df: pd.DataFrame) -> go.Figure:
    """
    Area chart reflecting the day-by-day submission rate.
    """
    if df.empty:
        fig = px.area(x=[datetime.now().strftime("%Y-%m-%d")], y=[0])
        return apply_glass_theme(fig, "Daily Incident Volume")
        
    df_copy = df.copy()
    # Safely convert and extract dates
    df_copy["date"] = pd.to_datetime(df_copy["timestamp"]).dt.strftime("%Y-%m-%d")
    daily = df_copy.groupby("date", as_index=False).size()
    daily.columns = ["Date", "Ticket Count"]
    
    # Sort date ascending
    daily = daily.sort_values("Date")
    
    fig = px.area(
        daily, 
        x="Date", 
        y="Ticket Count",
        markers=True
    )
    fig.update_traces(
        line_color="#9B59B6", 
        fillcolor="rgba(155, 89, 182, 0.15)",
        marker=dict(size=8, color="#FFFFFF", line=dict(color="#9B59B6", width=2))
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="New Incident Reports")
    return apply_glass_theme(fig, "Daily Incident Volume")

def get_all_charts_json() -> dict:
    """
    Helper for the FastAPI REST API to return Plotly configurations as serialized JSON.
    """
    df = load_tickets_df()
    return {
        "category_chart": json.loads(get_category_distribution_chart(df).to_json()),
        "priority_chart": json.loads(get_priority_distribution_chart(df).to_json()),
        "escalation_chart": json.loads(get_escalation_rate_chart(df).to_json()),
        "daily_chart": json.loads(get_daily_ticket_chart(df).to_json())
    }
