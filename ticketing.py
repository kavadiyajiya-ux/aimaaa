import os
import csv
import pandas as pd
import random
import string
from datetime import datetime

INCIDENTS_FILE = "incidents.csv"

# Columns matching the database and state schema
COLUMNS = [
    "ticket_id",
    "issue",
    "source",
    "category",
    "priority",
    "escalated",
    "escalation_contact",
    "response",
    "reasoning_trace",
    "timestamp",
    "sla_hours",
    "due_date",
    "status"
]

def generate_ticket_id(category: str) -> str:
    """
    Generates a unique Ticket ID following the format: CAT-YYYYMMDD-HEX4
    Example: IT-20260618-A1B2
    """
    prefix = {
        "IT": "IT",
        "HR": "HR",
        "Payroll": "PAY",
        "Security": "SEC",
        "Operations": "OPS"
    }.get(category, "GEN")
    
    # Format current date as 20260618
    date_str = "20260618" # Fixed to active date representation
    
    # Generate 4 character alphanumeric string in uppercase
    chars = string.ascii_uppercase + string.digits
    rand_str = "".join(random.choices(chars, k=4))
    
    return f"{prefix}-{date_str}-{rand_str}"

def initialize_database():
    """
    Creates the incidents.csv file if it doesn't exist and pre-populates it with historical tickets
    to populate charts and dashboards with realistic data.
    """
    if os.path.exists(INCIDENTS_FILE):
        return

    print("[Ticketing] Initializing incidents.csv database...")
    
    historical_tickets = [
        {
            "ticket_id": "IT-20260617-A1B2",
            "issue": "VPN access denied on connection attempt from home network",
            "source": "Gmail",
            "category": "IT",
            "priority": "Medium",
            "escalated": False,
            "escalation_contact": "",
            "response": "Your issue has been logged as Ticket IT-20260617-A1B2 and assigned to the IT Support Team. Estimated resolution time is 24 hours.",
            "reasoning_trace": "✓ Incident received\n✓ Memory retrieved\n✓ Category assigned\n✓ Priority calculated\n✓ Ticket generated\n✓ Escalation checked\n✓ Response generated",
            "timestamp": "2026-06-17 09:15:00",
            "sla_hours": 24,
            "due_date": "2026-06-18 09:15:00",
            "status": "In Progress"
        },
        {
            "ticket_id": "PAY-20260617-C3D4",
            "issue": "My monthly salary slip for May has an incorrect bonus calculation.",
            "source": "Employee Portal",
            "category": "Payroll",
            "priority": "High",
            "escalated": False,
            "escalation_contact": "",
            "response": "Your issue has been logged as Ticket PAY-20260617-C3D4 and assigned to the Payroll and Finance Team. Estimated resolution time is 8 hours.",
            "reasoning_trace": "✓ Incident received\n✓ Memory retrieved\n✓ Category assigned\n✓ Priority calculated\n✓ Ticket generated\n✓ Escalation checked\n✓ Response generated",
            "timestamp": "2026-06-17 10:20:00",
            "sla_hours": 8,
            "due_date": "2026-06-17 18:20:00",
            "status": "Resolved"
        },
        {
            "ticket_id": "SEC-20260617-E5F6",
            "issue": "ALERT: Suspicious ransomware note found on shared directory server SVR-09.",
            "source": "Employee Portal",
            "category": "Security",
            "priority": "Critical",
            "escalated": True,
            "escalation_contact": "security-manager@talenttech.com",
            "response": "CRITICAL INCIDENT: Logged as Ticket SEC-20260617-E5F6 and escalated to the Security Operations Center. A security engineer is analyzing the host. SLA: 4 hours.",
            "reasoning_trace": "✓ Incident received\n✓ Memory retrieved\n✓ Category assigned\n✓ Priority calculated\n✓ Ticket generated\n✓ Escalation checked\n✓ Response generated",
            "timestamp": "2026-06-17 11:30:00",
            "sla_hours": 4,
            "due_date": "2026-06-17 15:30:00",
            "status": "Resolved"
        },
        {
            "ticket_id": "HR-20260617-G7H8",
            "issue": "Leave request for annual vacation was rejected without feedback. Requesting appeal.",
            "source": "WhatsApp",
            "category": "HR",
            "priority": "Low",
            "escalated": False,
            "escalation_contact": "",
            "response": "Your issue has been logged as Ticket HR-20260617-G7H8 and assigned to the HR Relations Team. Estimated resolution time is 48 hours.",
            "reasoning_trace": "✓ Incident received\n✓ Memory retrieved\n✓ Category assigned\n✓ Priority calculated\n✓ Ticket generated\n✓ Escalation checked\n✓ Response generated",
            "timestamp": "2026-06-17 14:05:00",
            "sla_hours": 48,
            "due_date": "2026-06-19 14:05:00",
            "status": "Open"
        },
        {
            "ticket_id": "OPS-20260617-I9J0",
            "issue": "Internal mail server is completely unresponsive, unable to send/receive corporate mails.",
            "source": "Gmail",
            "category": "Operations",
            "priority": "Critical",
            "escalated": True,
            "escalation_contact": "operations-manager@talenttech.com",
            "response": "CRITICAL INCIDENT: Logged as Ticket OPS-20260617-I9J0 and escalated to the Operations Team. Core systems recovery is underway. SLA: 4 hours.",
            "reasoning_trace": "✓ Incident received\n✓ Memory retrieved\n✓ Category assigned\n✓ Priority calculated\n✓ Ticket generated\n✓ Escalation checked\n✓ Response generated",
            "timestamp": "2026-06-17 15:45:00",
            "sla_hours": 4,
            "due_date": "2026-06-17 19:45:00",
            "status": "In Progress"
        },
        {
            "ticket_id": "IT-20260616-K1L2",
            "issue": "Unable to log in to my laptop due to MFA verification code not sending to mobile device.",
            "source": "WhatsApp",
            "category": "IT",
            "priority": "Medium",
            "escalated": False,
            "escalation_contact": "",
            "response": "Your issue has been logged as Ticket IT-20260616-K1L2 and assigned to the IT Support Team. Estimated resolution time is 24 hours.",
            "reasoning_trace": "✓ Incident received\n✓ Memory retrieved\n✓ Category assigned\n✓ Priority calculated\n✓ Ticket generated\n✓ Escalation checked\n✓ Response generated",
            "timestamp": "2026-06-16 08:30:00",
            "sla_hours": 24,
            "due_date": "2026-06-17 08:30:00",
            "status": "Resolved"
        },
        {
            "ticket_id": "PAY-20260616-M3N4",
            "issue": "Salary not credited for the month of May yet. Please check.",
            "source": "Employee Portal",
            "category": "Payroll",
            "priority": "High",
            "escalated": False,
            "escalation_contact": "",
            "response": "Your issue has been logged as Ticket PAY-20260616-M3N4 and assigned to the Payroll and Finance Team. Estimated resolution time is 8 hours.",
            "reasoning_trace": "✓ Incident received\n✓ Memory retrieved\n✓ Category assigned\n✓ Priority calculated\n✓ Ticket generated\n✓ Escalation checked\n✓ Response generated",
            "timestamp": "2026-06-16 10:10:00",
            "sla_hours": 8,
            "due_date": "2026-06-16 18:10:00",
            "status": "Resolved"
        },
        {
            "ticket_id": "HR-20260616-O5P6",
            "issue": "Harassment complaint: Verbally abused by senior colleague during team meeting yesterday.",
            "source": "Employee Portal",
            "category": "HR",
            "priority": "Critical",
            "escalated": True,
            "escalation_contact": "hr-manager@talenttech.com",
            "response": "CRITICAL INCIDENT: Logged as Ticket HR-20260616-O5P6 and escalated to the HR Relations Team. An investigator will schedule a meeting with you today. SLA: 4 hours.",
            "reasoning_trace": "✓ Incident received\n✓ Memory retrieved\n✓ Category assigned\n✓ Priority calculated\n✓ Ticket generated\n✓ Escalation checked\n✓ Response generated",
            "timestamp": "2026-06-16 13:40:00",
            "sla_hours": 4,
            "due_date": "2026-06-16 17:40:00",
            "status": "In Progress"
        }
    ]

    with open(INCIDENTS_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for ticket in historical_tickets:
            writer.writerow(ticket)

def save_ticket(ticket_data: dict) -> None:
    """
    Appends a new ticket dict to the incidents.csv file.
    """
    initialize_database()
    
    # Fill in default values if missing
    ticket_row = {col: ticket_data.get(col, "") for col in COLUMNS}
    if not ticket_row["timestamp"]:
        ticket_row["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not ticket_row["status"]:
        ticket_row["status"] = "Open"
        
    # Standardize string representations of reasoning trace or memory if lists
    if isinstance(ticket_row["reasoning_trace"], list):
        ticket_row["reasoning_trace"] = "\n".join(ticket_row["reasoning_trace"])


    with open(INCIDENTS_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writerow(ticket_row)

def load_tickets() -> list:
    """
    Loads all tickets from incidents.csv as a list of dicts.
    """
    initialize_database()
    tickets = []
    try:
        with open(INCIDENTS_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert escalated back to boolean
                row["escalated"] = row["escalated"].lower() in ("true", "1", "yes")
                try:
                    row["sla_hours"] = int(row["sla_hours"]) if row["sla_hours"] else 0
                except ValueError:
                    row["sla_hours"] = 0
                tickets.append(row)
    except Exception as e:
        print(f"[Ticketing] Error loading tickets: {e}")
    return tickets

def load_tickets_df() -> pd.DataFrame:
    """
    Loads tickets as a Pandas DataFrame.
    """
    initialize_database()
    try:
        df = pd.read_csv(INCIDENTS_FILE)
        # Handle empty df case
        if df.empty:
            return pd.DataFrame(columns=COLUMNS)
        return df
    except Exception as e:
        print(f"[Ticketing] Error reading df: {e}")
        return pd.DataFrame(columns=COLUMNS)
