import pandas as pd
from datetime import datetime
from ticketing import load_tickets

def check_escalation(category: str, priority: str, issue: str) -> tuple[bool, str]:
    """
    Evaluates whether an incident must be escalated based on priority, category, and keyword rules.
    Returns: (is_escalated: bool, escalation_contact: str)
    """
    category_upper = category.upper()
    priority_upper = priority.upper()
    issue_lower = issue.lower()

    # Only critical incidents are automatically escalated
    if priority_upper == "CRITICAL":
        if "SECURITY" in category_upper or "breach" in issue_lower or "hack" in issue_lower or "leak" in issue_lower:
            return True, "security-manager@talenttech.com"
            
        if "HR" in category_upper and any(w in issue_lower for w in ["harass", "bully", "abuse", "discrimination"]):
            return True, "hr-manager@talenttech.com"
            
        if "OPERATIONS" in category_upper or "outage" in issue_lower or "server down" in issue_lower or "system down" in issue_lower:
            return True, "operations-manager@talenttech.com"
            
        # Default escalation contact for other critical issues
        return True, "support-director@talenttech.com"
        
    return False, ""

def get_escalation_logs() -> list[dict]:
    """
    Loads all incidents and returns only the escalated tickets formatted as escalation log entries.
    """
    tickets = load_tickets()
    escalated_tickets = []
    for t in tickets:
        if t.get("escalated"):
            # Clean reasoning trace to single-line or brief summary
            escalated_tickets.append({
                "ticket_id": t["ticket_id"],
                "timestamp": t["timestamp"],
                "category": t["category"],
                "priority": t["priority"],
                "escalation_contact": t["escalation_contact"],
                "issue": t["issue"],
                "status": t["status"]
            })
    # Sort by timestamp descending
    escalated_tickets.sort(key=lambda x: x["timestamp"], reverse=True)
    return escalated_tickets
