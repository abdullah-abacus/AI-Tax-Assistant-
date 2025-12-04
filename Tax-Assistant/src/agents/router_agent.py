"""
Router Agent using Google ADK + Gemini 2.5 Pro
LLM Agent that understands user intent and routes to correct workflow
"""
import os
from google.adk.agents import LlmAgent
from google.genai import types
from typing import Dict, Any

# Get API key from environment
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# System instruction for router agent
ROUTER_INSTRUCTION = """You are the Router Agent for KRA Tax Assistant.

Your role is to understand the user's intent and route to the correct workflow:

1. IT1 Filing: If user wants to file individual income tax return
2. VAT3 Filing: If user wants to file monthly VAT return  
3. General Query: For questions about tax procedures, forms, or requirements
4. Session Recovery: If user is continuing a previous session

Analyze the user's message and respond with a JSON object:
{
  "intent": "IT1_FILING" | "VAT3_FILING" | "QUERY" | "RECOVERY",
  "confidence": 0.0 to 1.0,
  "next_workflow": "filing_workflow" | "help" | "recovery"
}

CRITICAL RULES:
- Never mention audit processes or risk analysis to users
- Be friendly and professional
- Keep responses concise
- Always validate KRA PIN format before proceeding"""

def create_router_agent():
    """Create ADK Router Agent with Gemini 2.5 Pro"""
    
    # Configure Gemini model
    generate_config = types.GenerateContentConfig(
        temperature=0.3,  # Low temperature for consistent routing
        max_output_tokens=500,
        top_p=0.95,
        response_mime_type="application/json"  # Force JSON responses
    )
    
    # Create LLM Agent
    router = LlmAgent(
        model="gemini-2.5-pro",  # Use Gemini 2.5 Pro
        name="router_agent",
        instruction=ROUTER_INSTRUCTION,
        generate_content_config=generate_config
    )
    
    return router

def detect_intent_with_llm(user_message: str) -> Dict[str, Any]:
    """
    Use Gemini to detect user intent
    
    Args:
        user_message: User's input message
        
    Returns:
        Dictionary with intent, confidence, and next workflow
    """
    # NOTE: The ADK LlmAgent in this environment does not expose `.query`,
    # so we currently fall back to the rule-based detector for safety.
    # You can replace this with a direct google.genai client call similar
    # to `answer_tax_question` in `query_agent.py` if you want LLM-based routing.
    return fallback_intent_detection(user_message)

def fallback_intent_detection(user_message: str) -> Dict[str, Any]:
    """Fallback rule-based intent detection if LLM fails"""
    message_lower = user_message.lower()

    # If user explicitly says they have a question / need help (but not to file yet),
    # treat it as a general QUERY instead of starting a filing workflow.
    if any(keyword in message_lower for keyword in ['question', 'ask', 'help', 'info', 'information']) \
        and not any(keyword in message_lower for keyword in ['file', 'filing', 'return', 'submit', 'start']):
        return {
            "intent": "QUERY",
            "confidence": 0.8,
            "next_workflow": "help"
        }

    if any(keyword in message_lower for keyword in ['it1', 'income tax', 'individual tax', 'personal tax']):
        return {
            "intent": "IT1_FILING",
            "confidence": 0.9,
            "next_workflow": "filing_workflow"
        }
    
    if any(keyword in message_lower for keyword in ['vat3', 'vat', 'value added tax']):
        return {
            "intent": "VAT3_FILING",
            "confidence": 0.9,
            "next_workflow": "filing_workflow"
        }
    
    if any(keyword in message_lower for keyword in ['file', 'return', 'submit', 'declare']):
        return {
            "intent": "QUERY",
            "confidence": 0.6,
            "next_workflow": "help"
        }
    
    return {
        "intent": "QUERY",
        "confidence": 0.5,
        "next_workflow": "help"
    }

def get_greeting_message() -> str:
    """Return greeting message"""
    return """Hello! Welcome to the KRA Tax Assistant. 👋

I'm here to help you file your tax returns easily.

Which return would you like to file today?
- IT1 (Individual Income Tax)
- VAT3 (Monthly VAT)"""

def get_help_message() -> str:
    """Return help message"""
    return """I can help you file:
    
1. **IT1** - Individual Resident Income Tax Return
2. **VAT3** - Monthly VAT Return

To get started, just say:
- "I want to file IT1 return"
- "I want to file VAT3 return"

I'll guide you through all required questions step by step."""

def get_clarification_message() -> str:
    """Return clarification request"""
    return """I'm not sure what you're looking for. 

I can help you file:
- **IT1** returns (Individual Income Tax)
- **VAT3** returns (Monthly VAT)

Which one would you like to file?"""


class RouterAgent:
    """Router Agent class wrapper for compatibility"""
    
    def __init__(self):
        self.name = "router_agent"
    
    def detect_intent(self, user_message: str) -> Dict[str, Any]:
        """Detect user intent from message using Gemini with rule-based fallback"""
        message_lower = user_message.lower()

        # HARD RULE 1: if user explicitly says they are *not* filing,
        # always treat it as a general query, even if "filing" word appears.
        if "not filing" in message_lower or "don't want to file" in message_lower or "do not want to file" in message_lower:
            return {
                'filing_type': '',
                'confidence': 0.95,
                'workflow': 'help'
            }

        # HARD RULE 2: if user explicitly says they have a question / need help
        # and does NOT clearly say they want to file/submit/start a return,
        # treat it as a general query (help), even if LLM thinks otherwise.
        if any(keyword in message_lower for keyword in ['question', 'ask', 'help', 'info', 'information']) \
            and not any(keyword in message_lower for keyword in ['file my', 'file it1', 'file vat3', 'start filing', 'submit return', 'start return']):
            return {
                'filing_type': '',           # Not starting a filing yet
                'confidence': 0.9,
                'workflow': 'help'           # Will be normalized to 'help_response' in route_to_workflow
            }

        try:
            # Try LLM-based intent detection first
            intent_data = detect_intent_with_llm(user_message)
        except Exception:
            # Fallback to simple keyword rules if LLM fails
            intent_data = fallback_intent_detection(user_message)

        return {
            'filing_type': intent_data['intent'].replace('_FILING', ''),
            'confidence': intent_data['confidence'],
            'workflow': intent_data['next_workflow']
        }
    
    def route_to_workflow(self, intent: Dict[str, Any]) -> str:
        """Route to appropriate workflow"""
        workflow = intent.get('workflow', 'help')
        # Normalize to values expected by the UI layer
        if workflow == "help":
            return "help_response"
        return workflow
    
    def get_greeting_message(self) -> str:
        """Get greeting message"""
        return get_greeting_message()
    
    def get_help_message(self) -> str:
        """Get help message"""
        return get_help_message()
    
    def get_clarification_message(self) -> str:
        """Get clarification message"""
        return get_clarification_message()
