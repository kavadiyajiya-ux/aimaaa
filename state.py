from typing import TypedDict, List

class AgentState(TypedDict):
    """
    State representing the lifecycle of an incident in AIMA.
    """
    issue: str                  # The original employee request/description
    source: str                 # Ingestion source (Gmail, WhatsApp, Employee Portal)
    memory: List[str]           # Top 3 retrieved policy details (RAG)
    category: str               # Classified category (IT, HR, Payroll, Security, Operations)
    priority: str               # Calculated priority (Low, Medium, High, Critical)
    ticket_id: str              # Generated Ticket ID
    escalated: bool             # Flag indicating if the incident was escalated
    escalation_contact: str     # Target email address for escalation
    response: str               # The generated professional employee response
    reasoning_trace: List[str]  # Step-by-step trace of actions executed
    sla_hours: int              # SLA resolution time in hours
    due_date: str               # Due date calculated for resolution
