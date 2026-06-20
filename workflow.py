import os
from datetime import datetime
from langgraph.graph import StateGraph, END
from state import AgentState
from models import aima_client
from memory import retrieve_relevant_policies
from tools import calculate_sla, calculate_due_date
from ticketing import generate_ticket_id, save_ticket
from escalation import check_escalation

def ingest_incident(state: AgentState) -> dict:
    """
    Step 1: Ingest the employee issue. Detect source/channel if not provided.
    """
    issue = state.get("issue", "").strip()
    source = state.get("source", "").strip()
    
    if not source:
        # Detect channel source based on indicators
        issue_lower = issue.lower()
        if issue.startswith("+") or (any(c.isdigit() for c in issue[:6]) and ":" in issue[:20]):
            source = "WhatsApp"
        elif "subject:" in issue_lower or "from:" in issue_lower or "sender:" in issue_lower or "@" in issue[:40]:
            source = "Gmail"
        else:
            source = "Employee Portal"
            
    trace = ["✓ Incident received"]
    
    return {
        "source": source,
        "reasoning_trace": trace
    }

def retrieve_memory(state: AgentState) -> dict:
    """
    Step 2: Semantic policy search (RAG) using local memory.
    """
    issue = state.get("issue", "")
    # Retrieve top 3 policies matching the issue description
    policies = retrieve_relevant_policies(issue, limit=3)
    
    current_trace = state.get("reasoning_trace", [])
    updated_trace = current_trace + ["✓ Memory retrieved"]
    
    return {
        "memory": policies,
        "reasoning_trace": updated_trace
    }

def classify_incident(state: AgentState) -> dict:
    """
    Step 3: Auto-classify category (IT, HR, Payroll, Security, Operations) via LLM.
    """
    issue = state.get("issue", "")
    category = aima_client.classify_incident(issue)
    
    current_trace = state.get("reasoning_trace", [])
    updated_trace = current_trace + ["✓ Category assigned"]
    
    return {
        "category": category,
        "reasoning_trace": updated_trace
    }

def assess_priority(state: AgentState) -> dict:
    """
    Step 4: Assess Priority (Low, Medium, High, Critical) via LLM and heuristics.
    """
    issue = state.get("issue", "")
    category = state.get("category", "IT")
    
    priority = aima_client.assess_priority(issue, category)
    
    current_trace = state.get("reasoning_trace", [])
    updated_trace = current_trace + ["✓ Priority calculated"]
    
    return {
        "priority": priority,
        "reasoning_trace": updated_trace
    }

def generate_ticket(state: AgentState) -> dict:
    """
    Step 5: Allocate unique ticket ID and calculate SLA / due date targets.
    """
    category = state.get("category", "IT")
    priority = state.get("priority", "Low")
    
    ticket_id = generate_ticket_id(category)
    sla = calculate_sla(category, priority)
    
    # Calculate due date based on current timestamp
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    due_date = calculate_due_date(now_str, sla)
    
    current_trace = state.get("reasoning_trace", [])
    updated_trace = current_trace + ["✓ Ticket generated"]
    
    return {
        "ticket_id": ticket_id,
        "sla_hours": sla,
        "due_date": due_date,
        "reasoning_trace": updated_trace
    }

def escalate_incident(state: AgentState) -> dict:
    """
    Step 6: Check critical escalation guidelines and assign managers.
    """
    category = state.get("category", "IT")
    priority = state.get("priority", "Low")
    issue = state.get("issue", "")
    
    escalated, contact = check_escalation(category, priority, issue)
    
    current_trace = state.get("reasoning_trace", [])
    updated_trace = current_trace + ["✓ Escalation checked"]
    
    return {
        "escalated": escalated,
        "escalation_contact": contact,
        "reasoning_trace": updated_trace
    }

def generate_employee_response(state: AgentState) -> dict:
    """
    Step 7: Formulate professional response citing matching policies.
    """
    issue = state.get("issue", "")
    category = state.get("category", "IT")
    priority = state.get("priority", "Low")
    ticket_id = state.get("ticket_id", "")
    policies = state.get("memory", [])
    
    response = aima_client.generate_response(issue, category, priority, ticket_id, policies)
    
    current_trace = state.get("reasoning_trace", [])
    updated_trace = current_trace + ["✓ Response generated"]
    
    return {
        "response": response,
        "reasoning_trace": updated_trace
    }

def store_analytics(state: AgentState) -> dict:
    """
    Step 8: Save ticket logs and complete workflow.
    """
    # Create copy of state and call save
    ticket_data = dict(state)
    save_ticket(ticket_data)
    
    return {}

# Define LangGraph Orchestration StateGraph
workflow_builder = StateGraph(AgentState)

# Add Nodes
workflow_builder.add_node("ingest_incident", ingest_incident)
workflow_builder.add_node("retrieve_memory", retrieve_memory)
workflow_builder.add_node("classify_incident", classify_incident)
workflow_builder.add_node("assess_priority", assess_priority)
workflow_builder.add_node("generate_ticket", generate_ticket)
workflow_builder.add_node("escalate_incident", escalate_incident)
workflow_builder.add_node("generate_employee_response", generate_employee_response)
workflow_builder.add_node("store_analytics", store_analytics)

# Define Transitions
workflow_builder.set_entry_point("ingest_incident")
workflow_builder.add_edge("ingest_incident", "retrieve_memory")
workflow_builder.add_edge("retrieve_memory", "classify_incident")
workflow_builder.add_edge("classify_incident", "assess_priority")
workflow_builder.add_edge("assess_priority", "generate_ticket")
workflow_builder.add_edge("generate_ticket", "escalate_incident")
workflow_builder.add_edge("escalate_incident", "generate_employee_response")
workflow_builder.add_edge("generate_employee_response", "store_analytics")
workflow_builder.add_edge("store_analytics", END)

# Compile Graph
aima_graph = workflow_builder.compile()

def run_incident_workflow(issue: str, source: str = None) -> dict:
    """
    Runs the complete state graph workflow for a new incident issue.
    Returns: The final state dictionary.
    """
    initial_state = {
        "issue": issue,
        "source": source or "",
        "memory": [],
        "category": "",
        "priority": "",
        "ticket_id": "",
        "escalated": False,
        "escalation_contact": "",
        "response": "",
        "reasoning_trace": [],
        "sla_hours": 0,
        "due_date": ""
    }
    
    # Run the graph synchronously
    final_state = aima_graph.invoke(initial_state)
    return final_state
