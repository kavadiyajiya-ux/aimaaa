import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="AIMA – AI Incident Management Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports from custom codebase
from workflow import run_incident_workflow
from ticketing import load_tickets_df, initialize_database
from tools import get_incident_statistics
from analytics import (
    get_category_distribution_chart,
    get_priority_distribution_chart,
    get_escalation_rate_chart,
    get_daily_ticket_chart
)
from escalation import get_escalation_logs

# Ensure DB initialized
initialize_database()

# Session State Initialization
if "processed_ticket" not in st.session_state:
    st.session_state.processed_ticket = None

# Custom CSS Injection for Dark Glassmorphism Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');
    
    /* General styles */
    .stApp {
        background-color: #0b0e14;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(138, 63, 252, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(0, 254, 181, 0.05) 0%, transparent 45%);
        background-attachment: fixed;
        color: #f0f4f8;
        font-family: 'Inter', sans-serif;
    }
    
    /* Text font family overrides */
    h1, h2, h3, .stHeader {
        font-family: 'Outfit', sans-serif;
        color: #ffffff !important;
    }
    
    /* Glass card container */
    .glass-card {
        background: rgba(22, 27, 38, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 1.2rem !important;
        animation: fadeIn 0.6s cubic-bezier(0.22, 1, 0.36, 1);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Simple custom trace list container */
    .trace-box {
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.04);
        padding: 12px;
        border-radius: 8px;
        font-size: 0.9rem;
        color: #a0aec0;
        margin-bottom: 1rem;
    }
    
    .trace-step {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        animation: fadeIn 0.4s ease-out forwards;
    }
    
    .trace-check {
        color: #00feb5;
        font-weight: bold;
    }

    /* Output text area */
    .response-box {
        background: rgba(138, 63, 252, 0.05);
        border: 1px solid rgba(138, 63, 252, 0.15);
        padding: 15px;
        border-radius: 8px;
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.5;
        margin-top: 5px;
    }

    /* Badge styles */
    .stBadge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 5px;
    }
    
    /* Center text alignments */
    .center-text {
        text-align: center;
    }

    /* Metric modifications */
    div[data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #94a3b8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px;
    }
    </style>
    <style>
    /* ====== CSS VARIABLES ====== */
    :root {
        --accent-primary: #8a3ffc;
        --accent-secondary: #00feb5;
        --accent-blue: #0f62fe;
        --color-critical: #da1e28;
        --color-high: #ff832b;
        --color-medium: #f1c40f;
        --color-low: #198038;
        --text-muted: #94a3b8;
        --glass-border: rgba(255,255,255,0.06);
    }

    /* ====== SIDEBAR ====== */
    [data-testid="stSidebar"] {
        background: rgba(11, 14, 20, 0.95) !important;
        border-right: 1px solid var(--glass-border) !important;
    }

    /* ====== TABS ====== */
    [data-testid="stTabs"] [role="tab"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
        color: var(--text-muted) !important;
        border-radius: 6px 6px 0 0 !important;
        transition: color 0.2s !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: var(--accent-secondary) !important;
        border-bottom-color: var(--accent-secondary) !important;
    }
    [data-testid="stTabs"] [role="tabpanel"] {
        background: transparent !important;
        padding-top: 1rem !important;
    }

    /* ====== BUTTONS ====== */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-blue)) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 4px 15px rgba(138, 63, 252, 0.3) !important;
        transition: opacity 0.2s, transform 0.1s !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
    }
    .stDownloadButton > button {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid var(--glass-border) !important;
        color: #fff !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }

    /* ====== FORM INPUTS ====== */
    .stTextArea textarea, .stSelectbox select, [data-testid="stTextArea"] textarea {
        background: rgba(0,0,0,0.25) !important;
        border: 1px solid var(--glass-border) !important;
        color: #f0f4f8 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextArea textarea:focus, .stSelectbox:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(138,63,252,0.2) !important;
    }

    /* ====== SELECTBOX ====== */
    [data-testid="stSelectbox"] > div > div {
        background: rgba(0,0,0,0.25) !important;
        border: 1px solid var(--glass-border) !important;
        color: #f0f4f8 !important;
        border-radius: 8px !important;
    }

    /* ====== MULTISELECT ====== */
    [data-testid="stMultiSelect"] > div > div {
        background: rgba(0,0,0,0.25) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 8px !important;
    }

    /* ====== DATAFRAME ====== */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--glass-border) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    [data-testid="stDataFrame"] th {
        background: rgba(255,255,255,0.03) !important;
        color: #fff !important;
        font-weight: 600 !important;
    }
    [data-testid="stDataFrame"] td {
        color: #e2e8f0 !important;
    }

    /* ====== ALERTS / INFO / SUCCESS / ERROR ====== */
    [data-testid="stAlert"] {
        border-radius: 8px !important;
    }

    /* ====== SPINNER ====== */
    [data-testid="stSpinner"] {
        color: var(--accent-secondary) !important;
    }

    /* ====== SUBHEADERS ====== */
    [data-testid="stHeading"] h2,
    [data-testid="stHeading"] h3 {
        color: #ffffff !important;
        font-family: 'Outfit', sans-serif !important;
        border-bottom: 1px solid var(--glass-border);
        padding-bottom: 6px;
        margin-bottom: 10px;
    }

    /* ====== SCROLLBAR ====== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
    </style>
""", unsafe_allow_html=True)

# Application Header HTML
st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 15px; margin-bottom: 25px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #8a3ffc, #0f62fe); display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; font-size: 1.4rem; box-shadow: 0 0 20px rgba(138,63,252,0.4);">A</div>
            <div>
                <h1 style="margin: 0; font-size: 1.7rem; font-weight: 700; background: linear-gradient(to right, #ffffff, #a5b4fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AIMA</h1>
                <p style="margin: 0; font-size: 0.8rem; color: #94a3b8;">AI-Driven Incident Management Assistant | Enterprise Support</p>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.85rem; color: #94a3b8; border: 1px solid rgba(255,255,255,0.06); padding: 4px 12px; border-radius: 20px; background: rgba(255,255,255,0.01);">
                ⏰ System Date: <strong>2026-06-18</strong>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# KPI Cards layout
stats = get_incident_statistics()
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
        <div style="background: rgba(22, 27, 38, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.2rem; border-radius: 10px; border-left: 4px solid #3A86C8; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h3 style="margin: 0; font-size: 2rem; color: #fff; font-family:'Outfit';">{stats['total_incidents']}</h3>
            <p style="margin: 0; font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; font-family:'Inter';">Total Incidents</p>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div style="background: rgba(22, 27, 38, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.2rem; border-radius: 10px; border-left: 4px solid #E67E22; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h3 style="margin: 0; font-size: 2rem; color: #fff; font-family:'Outfit';">{stats['escalated_incidents']}</h3>
            <p style="margin: 0; font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; font-family:'Inter';">Escalated Logs</p>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div style="background: rgba(22, 27, 38, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.2rem; border-radius: 10px; border-left: 4px solid #E74C3C; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h3 style="margin: 0; font-size: 2rem; color: #fff; font-family:'Outfit';">{stats['critical_incidents']}</h3>
            <p style="margin: 0; font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; font-family:'Inter';">Critical Alerts</p>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
        <div style="background: rgba(22, 27, 38, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.2rem; border-radius: 10px; border-left: 4px solid #8a3ffc; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h3 style="margin: 0; font-size: 2rem; color: #fff; font-family:'Outfit';">{stats['avg_resolution_time_hours']}h</h3>
            <p style="margin: 0; font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; font-family:'Inter';">Avg SLA Target</p>
        </div>
    """, unsafe_allow_html=True)

st.write("") # Spacer

# Main layout splitting
left_col, right_col = st.columns([1, 2])

# Left Column: Incident Submission & Live Agent Triage
with left_col:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📥 Log New Employee Incident")
    
    with st.form("incident_submission_form", clear_on_submit=False):
        issue_input = st.text_area(
            "Incident Description", 
            placeholder="Describe the employee issue in detail (e.g. My salary payment for this month was not credited. Direct deposit details are correct...)",
            height=120
        )
        
        channel_input = st.selectbox(
            "Communication Channel (Auto-detection supported)",
            options=["Auto-Detect", "Employee Portal", "Gmail", "WhatsApp"]
        )
        
        submit_btn = st.form_submit_button("Launch Intelligent Triage Agent")
        
        if submit_btn:
            if not issue_input.strip():
                st.error("Please enter a description of the incident before submitting.")
            else:
                src = None if channel_input == "Auto-Detect" else channel_input
                with st.spinner("Executing LangGraph agent nodes..."):
                    try:
                        final_state = run_incident_workflow(issue_input, src)
                        st.session_state.processed_ticket = final_state
                        st.toast(f"✅ Ticket Generated: {final_state.get('ticket_id')}", icon="🤖")
                        st.rerun() # Refresh layout to load metrics and lists
                    except Exception as e:
                        st.error(f"Error processing workflow: {e}")
                        
    st.markdown('</div>', unsafe_allow_html=True)

    # Display live result details if available
    if st.session_state.processed_ticket:
        t = st.session_state.processed_ticket
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🕵️ Live Agent Reasoning Trace")
        
        # Display trace steps
        trace = t.get("reasoning_trace", [])
        if isinstance(trace, str):
            trace = trace.split("\n")
            
        trace_html = '<div class="trace-box">'
        for step in trace:
            clean_step = step.lstrip("✓").strip()
            trace_html += f'<div class="trace-step"><span class="trace-check">✓</span> {clean_step}</div>'
        trace_html += '</div>'
        st.markdown(trace_html, unsafe_allow_html=True)
        
        # Ticket info block
        st.subheader("🎫 Ticket Triage Metadata")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.write(f"**Ticket ID:** `{t.get('ticket_id')}`")
            st.write(f"**Category:** `{t.get('category')}`")
            st.write(f"**Source:** `{t.get('source')}`")
        with t_col2:
            st.write(f"**Priority:** `{t.get('priority')}`")
            st.write(f"**SLA Duration:** `{t.get('sla_hours')} hours`")
            st.write(f"**Due Date:** `{t.get('due_date')}`")
            
        if t.get("escalated"):
            st.markdown(f"""
                <div style="background: rgba(218, 30, 40, 0.1); border: 1px solid var(--color-critical); padding: 10px; border-radius: 8px; font-size: 0.85rem; color: #ff8a80; margin-bottom: 15px;">
                    🚨 <strong>Critical Escalation Triggered!</strong> Incident escalated to <code>{t.get('escalation_contact')}</code>
                </div>
            """, unsafe_allow_html=True)
            
        # RAG memory context
        st.subheader("📖 Retrieved Policy Context (RAG)")
        mem = t.get("memory", [])
        if mem:
            for i, policy in enumerate(mem):
                st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 6px; font-size: 0.8rem; margin-bottom: 8px;">
                        {policy}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No policy documents matched query parameters.")

        # Final Response Box
        st.subheader("✉️ Generated Employee Response")
        st.markdown(f'<div class="response-box">{t.get("response")}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Right Column: Dashboard Tabs & Historical Lists
with right_col:
    # Setup tabs
    tab_rep, tab_charts, tab_kb, tab_escalations = st.tabs([
        "📁 Ticket Repository",
        "📊 Analytics Hub",
        "📖 Policy Knowledge Base",
        "🚨 Escalation Logs"
    ])
    
    # Tab 1: Ticket Repository
    with tab_rep:
        st.subheader("Logged Ticket Repository")
        df_incidents = load_tickets_df()
        
        if df_incidents.empty:
            st.info("No incident records logged in system yet.")
        else:
            # Layout filtering controls
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                sel_cat = st.multiselect("Filter by Category", options=df_incidents["category"].unique())
            with f_col2:
                sel_prio = st.multiselect("Filter by Priority", options=df_incidents["priority"].unique())
            with f_col3:
                sel_status = st.multiselect("Filter by Status", options=df_incidents["status"].unique())
                
            # Filter logic
            filtered_df = df_incidents.copy()
            if sel_cat:
                filtered_df = filtered_df[filtered_df["category"].isin(sel_cat)]
            if sel_prio:
                filtered_df = filtered_df[filtered_df["priority"].isin(sel_prio)]
            if sel_status:
                filtered_df = filtered_df[filtered_df["status"].isin(sel_status)]
                
            # Display table with column_config styling
            st.dataframe(
                filtered_df[[
                    "ticket_id", "timestamp", "issue", "source", "category", 
                    "priority", "escalated", "escalation_contact", "status"
                ]].sort_values("timestamp", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ticket_id": st.column_config.TextColumn("Ticket ID", width="medium"),
                    "priority": st.column_config.TextColumn("Priority"),
                    "escalated": st.column_config.CheckboxColumn("Escalated", default=False),
                    "status": st.column_config.TextColumn("Status")
                }
            )
            
            # Action controls
            st.write("")
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                # Export CSV
                csv_data = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Export Report (CSV)",
                    data=csv_data,
                    file_name=f"aima_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            with act_col2:
                # Export JSON
                json_data = filtered_df.to_json(orient="records", indent=2)
                st.download_button(
                    label="📥 Export Database (JSON)",
                    data=json_data,
                    file_name=f"aima_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
    # Tab 2: Analytics Hub
    with tab_charts:
        st.subheader("AI Incident Analytics Dashboard")
        df_incidents = load_tickets_df()
        
        if df_incidents.empty:
            st.info("Insufficient ticket data for analytics computation.")
        else:
            # First row: Category and Priority
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                fig_cat = get_category_distribution_chart(df_incidents)
                st.plotly_chart(fig_cat, use_container_width=True)
            with c_col2:
                fig_prio = get_priority_distribution_chart(df_incidents)
                st.plotly_chart(fig_prio, use_container_width=True)
                
            # Second row: Escalation and Daily Ticket Counts
            c_col3, c_col4 = st.columns(2)
            with c_col3:
                fig_esc = get_escalation_rate_chart(df_incidents)
                st.plotly_chart(fig_esc, use_container_width=True)
            with c_col4:
                fig_daily = get_daily_ticket_chart(df_incidents)
                st.plotly_chart(fig_daily, use_container_width=True)

    # Tab 3: Policy Knowledge Base
    with tab_kb:
        st.subheader("Enterprise Policies repository")
        POLICIES_CSV = "policies.csv"
        if os.path.exists(POLICIES_CSV):
            df_policies = pd.read_csv(POLICIES_CSV)
            st.dataframe(
                df_policies,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Policies CSV repository is missing. Run server initialization first.")

    # Tab 4: Escalation Logs
    with tab_escalations:
        st.subheader("Critical Incident Escalation Registry")
        logs = get_escalation_logs()
        
        if not logs:
            st.info("No escalated incidents recorded.")
        else:
            for idx, log in enumerate(logs):
                st.markdown(f"""
                    <div style="background: rgba(218, 30, 40, 0.05); border: 1px solid rgba(218, 30, 40, 0.15); border-left: 5px solid var(--color-critical); padding: 15px; border-radius: 8px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="font-weight: 700; color: #fff; font-size: 0.95rem;">🎟️ Ticket: {log['ticket_id']}</span>
                            <span style="font-size: 0.8rem; color: #94a3b8;">🕒 Escalated: {log['timestamp']}</span>
                        </div>
                        <p style="font-size: 0.9rem; color: #e2e8f0; margin-bottom: 8px;"><strong>Issue Details:</strong> "{log['issue']}"</p>
                        <div style="display: flex; gap: 15px; font-size: 0.82rem; color: #a0aec0;">
                            <span>📁 Category: <strong>{log['category']}</strong></span>
                            <span>⚡ Priority: <strong style="color:var(--color-critical);">{log['priority']}</strong></span>
                            <span>📨 Assigned: <code>{log['escalation_contact']}</code></span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
