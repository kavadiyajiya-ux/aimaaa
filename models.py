import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Configuration keys
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

# Check if a valid API key is present
IS_LLM_ACTIVE = bool(OPENAI_API_KEY and not OPENAI_API_KEY.startswith("your_"))

class FallbackEngine:
    """
    Robust rule-based logic to serve as a high-quality fallback when LLM is unavailable.
    """
    @staticmethod
    def classify(issue: str) -> str:
        issue_lower = issue.lower()
        if any(w in issue_lower for w in ["breach", "leak", "unauthorized", "hack", "security", "malware", "virus", "incident"]):
            if any(w in issue_lower for w in ["vpn", "login", "password"]):
                # check if it's a minor login thing or serious breach
                if "breach" in issue_lower or "leak" in issue_lower or "hack" in issue_lower:
                    return "Security"
                return "IT"
            return "Security"
        if any(w in issue_lower for w in ["harass", "bully", "abuse", "threat", "conduct"]):
            return "HR"
        if any(w in issue_lower for w in ["server down", "outage", "system down", "network down", "database offline", "crashed", "timeout", "databases are completely down"]):
            return "Operations"
        if any(w in issue_lower for w in ["salary", "pay", "credited", "payslip", "deposit", "finance"]):
            return "Payroll"
        if any(w in issue_lower for w in ["leave", "vacation", "holiday", "absence", "sick"]):
            return "HR"
        if any(w in issue_lower for w in ["vpn", "login", "password", "mfa", "authenticator", "wifi", "internet", "laptop", "pc", "software", "outlook"]):
            return "IT"
        return "IT"

    @staticmethod
    def assess_priority(issue: str, category: str) -> str:
        issue_lower = issue.lower()
        # Security Breach, Harassment, System Outages -> Critical
        if category == "Security" or "breach" in issue_lower or "data breach" in issue_lower or "leak" in issue_lower:
            return "Critical"
        if "harass" in issue_lower or "bully" in issue_lower or "abuse" in issue_lower:
            return "Critical"
        if category == "Operations" and any(w in issue_lower for w in ["outage", "down", "offline", "crash"]):
            return "Critical"
        # Salary delays -> High
        if category == "Payroll" and any(w in issue_lower for w in ["delay", "missing", "not credited", "not received", "not been credited"]):
            return "High"
        # VPN / IT login issues -> Medium
        if category == "IT" and any(w in issue_lower for w in ["vpn", "login", "mfa", "authenticator", "password"]):
            return "Medium"
        return "Low"

    @staticmethod
    def generate_response(issue: str, category: str, priority: str, ticket_id: str, policies: list) -> str:
        policy_text = ""
        if policies:
            policy_text = " According to corporate policy: " + " ".join(policies[:2])
        
        sla_hours = 48
        if priority == "Critical":
            sla_hours = 4
        elif priority == "High":
            sla_hours = 8
        elif priority == "Medium":
            sla_hours = 24
            
        role_map = {
            "IT": "IT Support Team",
            "HR": "HR Relations Team",
            "Payroll": "Payroll and Finance Team",
            "Security": "Security Operations Center",
            "Operations": "Infrastructure Operations Team"
        }
        team = role_map.get(category, "Operations Support Team")
        
        response = f"Your issue has been logged as Ticket {ticket_id} and assigned to the {team}. "
        response += f"Estimated resolution time (SLA) is {sla_hours} hours.{policy_text} "
        response += "A technician will reach out shortly to provide updates. Thank you for your patience."
        return response

class AIMAClient:
    def __init__(self):
        self.llm = None
        if IS_LLM_ACTIVE:
            try:
                self.llm = ChatOpenAI(
                    openai_api_base=OPENAI_API_BASE,
                    openai_api_key=OPENAI_API_KEY,
                    model_name=OPENAI_MODEL,
                    temperature=0.1,
                    max_tokens=400
                )
            except Exception as e:
                print(f"[AIMA LLM] Failed to initialize ChatOpenAI client: {e}. Falling back to Rule-Based Heuristics.")
                self.llm = None

    def classify_incident(self, issue: str) -> str:
        if not self.llm:
            return FallbackEngine.classify(issue)
        
        prompt = PromptTemplate.from_template(
            "You are an Incident Classification AI. Classify the following employee issue into exactly one of these categories: "
            "IT, HR, Payroll, Security, Operations.\n"
            "Rules:\n"
            "- VPN, MFA, login, laptops, passwords, software access -> IT\n"
            "- Salary, payslips, direct deposit, taxes -> Payroll\n"
            "- Leave approval, harassment, workplace environment, HR portal -> HR\n"
            "- Data breaches, malware, leaked credentials, phishing -> Security\n"
            "- Network outages, server down, infrastructure failures -> Operations\n\n"
            "Issue: {issue}\n\n"
            "Response should only be the category name (IT, HR, Payroll, Security, or Operations)."
        )
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({"issue": issue})
            category = result.content.strip()
            # Clean response
            for val in ["IT", "HR", "Payroll", "Security", "Operations"]:
                if val.lower() in category.lower():
                    return val
            return FallbackEngine.classify(issue)
        except Exception as e:
            print(f"[LLM Error] Classify failed: {e}. Fallback triggered.")
            return FallbackEngine.classify(issue)

    def assess_priority(self, issue: str, category: str) -> str:
        if not self.llm:
            return FallbackEngine.assess_priority(issue, category)
        
        prompt = PromptTemplate.from_template(
            "You are an Incident Priority Evaluator. Determine the priority (Low, Medium, High, Critical) of the incident.\n"
            "Rules:\n"
            "- Security Breach, Harassment, or major System Outage/Production down -> Critical\n"
            "- Salary delays or critical payroll blocker -> High\n"
            "- VPN issues, MFA failures, login blockers -> Medium\n"
            "- Leave requests, general policy inquiry, simple laptop upgrades -> Low\n\n"
            "Category: {category}\n"
            "Issue: {issue}\n\n"
            "Response should only be the priority level (Low, Medium, High, or Critical)."
        )
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({"issue": issue, "category": category})
            priority = result.content.strip()
            for val in ["Low", "Medium", "High", "Critical"]:
                if val.lower() in priority.lower():
                    return val
            return FallbackEngine.assess_priority(issue, category)
        except Exception as e:
            print(f"[LLM Error] Priority assess failed: {e}. Fallback triggered.")
            return FallbackEngine.assess_priority(issue, category)

    def generate_response(self, issue: str, category: str, priority: str, ticket_id: str, policies: list) -> str:
        if not self.llm:
            return FallbackEngine.generate_response(issue, category, priority, ticket_id, policies)
        
        policy_context = "\n".join([f"- {p}" for p in policies])
        
        prompt = PromptTemplate.from_template(
            "You are an Employee Support Coordinator writing a professional email/message response to an employee incident ticket.\n"
            "Write a concise, professional, and empathetic response informing the employee of their logged ticket details.\n\n"
            "Ticket Information:\n"
            "- Ticket ID: {ticket_id}\n"
            "- Category: {category}\n"
            "- Priority: {priority}\n"
            "- Original Issue: {issue}\n\n"
            "Relevant Corporate Policies:\n"
            "{policy_context}\n\n"
            "Instructions:\n"
            "- Mention the Ticket ID.\n"
            "- Explicitly mention the department or support team handling it (e.g. IT support, HR relations, Security Center, Operations).\n"
            "- Mention the resolution SLA based on priority (Critical: 4 hours, High: 8 hours, Medium: 24 hours, Low: 48 hours).\n"
            "- Cite instructions from the relevant corporate policies to assist them immediately if applicable.\n"
            "- Do not use placeholders. Do not exceed 4 sentences."
        )
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({
                "ticket_id": ticket_id,
                "category": category,
                "priority": priority,
                "issue": issue,
                "policy_context": policy_context
            })
            return result.content.strip()
        except Exception as e:
            print(f"[LLM Error] Response generation failed: {e}. Fallback triggered.")
            return FallbackEngine.generate_response(issue, category, priority, ticket_id, policies)

# Singleton client instance
aima_client = AIMAClient()
