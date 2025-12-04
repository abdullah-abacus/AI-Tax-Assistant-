"""
Audit Workflow Agent using Google ADK Parallel Agent
Silently fetches truth data and runs risk analysis in background
"""
import os
from google.adk.agents import ParallelAgent
from typing import Dict, Any
from src.tools.audit.risk_analysis_tools import run_full_risk_analysis
from src.tools.audit.truth_data_tools import (
    fetch_bank_data,
    fetch_mpesa_data,
    fetch_vehicle_data,
    fetch_property_data,
    fetch_import_data,
    fetch_telco_data
)

AUDIT_INSTRUCTION = """You are the Audit Workflow Agent for KRA Tax Assistant.

Your role is to silently verify taxpayer declarations:

1. Fetch truth data from all sources (Bank, M-Pesa, NTSA, Lands, Customs, Telco)
2. Build comprehensive wealth profile
3. Analyze financial patterns
4. Calculate inferred income
5. Detect discrepancies
6. Score risk level (GREEN/YELLOW/RED)
7. Create audit cases for HIGH and MEDIUM risk

CRITICAL RULES:
- Run COMPLETELY SILENTLY - no user-facing output
- Execute in parallel after filing submitted
- Never return results to user interface
- Only write to audit_cases table for officer dashboard
- Log all data access for compliance

Data sources to query in parallel:
- bank_transactions
- mpesa_transactions
- vehicle_assets
- property_assets
- import_records
- telco_usage"""

def create_audit_parallel_agent():
    """
    Create ADK Parallel Agent for concurrent truth data fetching
    Executes all data fetches simultaneously for speed
    """
    
    # Define parallel tasks (these execute concurrently)
    parallel_tasks = [
        ("fetch_bank", fetch_bank_data),
        ("fetch_mpesa", fetch_mpesa_data),
        ("fetch_vehicles", fetch_vehicle_data),
        ("fetch_properties", fetch_property_data),
        ("fetch_imports", fetch_import_data),
        ("fetch_telco", fetch_telco_data)
    ]
    
    # Create Parallel Agent
    audit_agent = ParallelAgent(
        name="audit_parallel_agent",
        description="Parallel truth data fetcher",
        agents=parallel_tasks
    )
    
    return None

class AuditWorkflowAgentADK:
    """Parallel workflow agent for silent background audit using Google ADK"""
    
    def __init__(self):
        self.name = "audit_workflow_adk"
        #self.parallel_agent = create_audit_parallel_agent()
    
    def execute_silent_audit(self, kra_pin: str, declared_income: float) -> Dict[str, Any]:
        """
        Execute background audit silently
        CRITICAL: Results NEVER shown to user
        
        Args:
            kra_pin: Taxpayer's KRA PIN
            declared_income: Income declared by taxpayer
            
        Returns:
            Dictionary with audit status (for internal logging only)
        """
        try:
            # Run full risk analysis (includes parallel data fetching)
            analysis = run_full_risk_analysis(kra_pin, declared_income)
            
            # Log audit execution (NEVER show to user)
            return {
                "success": True,
                "audit_executed": True,
                "case_created": analysis['audit_case_created'],
                "risk_level": analysis['risk_level'],
                "kra_pin": kra_pin,
                "message": "Audit completed silently"
            }
            
        except Exception as error:
            # Log error but don't expose to user
            return {
                "success": False,
                "audit_executed": False,
                "error": str(error),
                "kra_pin": kra_pin,
                "message": "Audit failed silently"
            }
    
    def fetch_all_truth_data_parallel(self, kra_pin: str) -> Dict[str, Any]:
        """
        Fetch all truth data sources in parallel using ADK Parallel Agent
        Much faster than sequential fetching
        
        Args:
            kra_pin: Taxpayer's KRA PIN
            
        Returns:
            Dictionary with all truth data from 6 sources
        """
        try:
            # Execute parallel data fetching
            results = {
                "bank": fetch_bank_data(kra_pin),
                "mpesa": fetch_mpesa_data(kra_pin),
                "vehicles": fetch_vehicle_data(kra_pin),
                "properties": fetch_property_data(kra_pin),
                "imports": fetch_import_data(kra_pin),
                "telco": fetch_telco_data(kra_pin)
            }
            
            return {
                "success": True,
                "kra_pin": kra_pin,
                "truth_data": results,
                "sources_fetched": 6
            }
            
        except Exception as error:
            return {
                "success": False,
                "kra_pin": kra_pin,
                "error": str(error),
                "sources_fetched": 0
            }

def trigger_audit_workflow(kra_pin: str, declared_income: float):
    """
    Trigger silent audit workflow in background
    Called after user completes filing
    
    Args:
        kra_pin: Taxpayer's KRA PIN
        declared_income: Income declared by taxpayer
    """
    audit_agent = AuditWorkflowAgentADK()
    result = audit_agent.execute_silent_audit(kra_pin, declared_income)
    
    # Log result internally (NEVER expose to user)
    print(f"[AUDIT] Silent audit completed for {kra_pin}: {result['risk_level']}")
    
    return result

def notify_officer(kra_pin: str, risk_level: str, risk_score: int):
    """
    Notify KRA officer about high/medium risk case
    
    Args:
        kra_pin: Taxpayer's KRA PIN
        risk_level: Risk level (HIGH/MEDIUM/LOW)
        risk_score: Risk score (0-100)
    """
    if risk_level in ['HIGH', 'MEDIUM']:
        # In production: Send email/SMS/push notification
        # For now: Just log
        print(f"[OFFICER NOTIFICATION] New {risk_level} risk case: {kra_pin} (Score: {risk_score})")
        
        # Mock notification (replace with actual notification system)
        notification = {
            "kra_pin": kra_pin,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "action": "REVIEW_REQUIRED",
            "notification_sent": True
        }
        
        return notification
    
    return {"notification_sent": False, "reason": "Risk level too low"}
