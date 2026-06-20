import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd

from workflow import run_incident_workflow
from ticketing import load_tickets, initialize_database
from tools import get_incident_statistics
from analytics import get_all_charts_json

# Initialize Ticket Database on startup
initialize_database()

app = FastAPI(
    title="AIMA Backend API",
    description="REST API powering the AI-Driven Incident Management Assistant",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema for Incident Ingestion
class IncidentSubmitRequest(BaseModel):
    issue: str
    source: Optional[str] = "Employee Portal"

# Incident response schemas
class IncidentResponse(BaseModel):
    ticket_id: str
    issue: str
    source: str
    category: str
    priority: str
    escalated: bool
    escalation_contact: str
    response: str
    reasoning_trace: List[str]
    sla_hours: int
    due_date: str

@app.get("/")
def read_root():
    """Redirect API root to static dashboard portal."""
    return RedirectResponse(url="/static/index.html")

@app.post("/api/incidents/submit", response_model=IncidentResponse)
def submit_incident(payload: IncidentSubmitRequest):
    """
    Submits a new employee issue, running the LangGraph agent orchestration workflow.
    """
    issue_text = payload.issue.strip()
    if not issue_text:
        raise HTTPException(status_code=400, detail="Incident issue description cannot be empty.")
        
    try:
        final_state = run_incident_workflow(issue_text, payload.source)
        # Ensure reasoning trace is format split
        trace = final_state.get("reasoning_trace", [])
        if isinstance(trace, str):
            trace = trace.split("\n")
            
        return IncidentResponse(
            ticket_id=final_state.get("ticket_id", ""),
            issue=final_state.get("issue", ""),
            source=final_state.get("source", ""),
            category=final_state.get("category", ""),
            priority=final_state.get("priority", ""),
            escalated=final_state.get("escalated", False),
            escalation_contact=final_state.get("escalation_contact", ""),
            response=final_state.get("response", ""),
            reasoning_trace=trace,
            sla_hours=final_state.get("sla_hours", 24),
            due_date=final_state.get("due_date", "")
        )
    except Exception as e:
        print(f"[API Error] Run workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Incident processing engine failed: {str(e)}")

@app.get("/api/tickets")
def get_tickets():
    """
    Retrieves the complete list of tickets logged in the system.
    """
    try:
        return load_tickets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading ticket records: {str(e)}")

@app.get("/api/analytics")
def get_analytics():
    """
    Returns general stats KPIs along with serialized Plotly charts JSON.
    """
    try:
        stats = get_incident_statistics()
        charts = get_all_charts_json()
        return {
            "statistics": stats,
            "charts": charts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compiling analytics: {str(e)}")

@app.get("/api/kb")
def get_knowledge_base():
    """
    Returns the loaded list of enterprise policies from policies.csv.
    """
    POLICIES_CSV = "policies.csv"
    if not os.path.exists(POLICIES_CSV):
        raise HTTPException(status_code=404, detail="Policies repository not found.")
        
    try:
        df = pd.read_csv(POLICIES_CSV)
        return df.to_dict("records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading policies: {str(e)}")

@app.get("/api/health")
def get_health_status():
    """
    Returns detailed diagnostics and status of subsystems.
    """
    incidents_exists = os.path.exists("incidents.csv")
    policies_exists = os.path.exists("policies.csv")
    chroma_exists = os.path.exists("chroma_db")
    
    # Try importing memory to see if ChromaDB is active or fallback
    try:
        from memory import policy_memory
        policy_memory.init_db()
        rag_status = "Fallback (Keyword Matcher Active)" if policy_memory.use_fallback else "Active (ChromaDB + SentenceTransformers)"
    except Exception as e:
        rag_status = f"Unavailable ({str(e)})"
        
    return {
        "status": "Healthy",
        "database": {
            "incidents_csv_present": incidents_exists,
            "policies_csv_present": policies_exists,
            "chromadb_dir_present": chroma_exists
        },
        "rag_engine": rag_status,
        "api_server": "Running"
    }

# Create static directory if missing
os.makedirs("static", exist_ok=True)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
