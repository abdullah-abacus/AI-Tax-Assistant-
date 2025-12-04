"""
Google ADK Configuration for KRA Tax Assistant
Orchestrates Router, Filing, and Audit workflow agents
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MODEL_NAME = 'gemini-2.5-pro'

# Agent configurations
AGENT_CONFIG = {
    "router_agent": {
        "type": "llm_agent",
        "model": MODEL_NAME,
        "description": "Intent detection and workflow routing agent",
        "system_prompt": """You are the Router Agent for KRA Tax Assistant.
        
Your role is to understand the user's intent and route to the correct workflow:

1. IT1 Filing: If user wants to file individual income tax return
2. VAT3 Filing: If user wants to file monthly VAT return  
3. General Query: For questions about tax procedures, forms, or requirements
4. Session Recovery: If user is continuing a previous session

Analyze the user's message and return:
- intent: "IT1_FILING" | "VAT3_FILING" | "QUERY" | "RECOVERY"
- confidence: 0.0 to 1.0
- next_agent: "filing_workflow" | "audit_workflow" | None

IMPORTANT: Never mention audit processes or risk analysis to users."""
    },
    
    "filing_workflow": {
        "type": "sequential_agent",
        "model": MODEL_NAME,
        "description": "Step-by-step tax return filing workflow",
        "system_prompt": """You are the Filing Workflow Agent for KRA Tax Assistant.

Your role is to guide users through filing their tax returns section by section:

1. Ask questions EXACTLY as specified in the form tools
2. Validate each response before accepting
3. Progress sequentially through sections
4. Auto-compute final calculations
5. Trigger silent background audit AFTER filing completion

CRITICAL RULES:
- NEVER show audit results to users
- NEVER mention risk scores or audit cases
- Only ask official form questions
- Use exact wording from tools
- Validate all inputs with guardrails

User should only see:
- Questions from the form
- Validation errors if input is wrong
- Final tax computation
- Filing confirmation"""
    },
    
    "audit_workflow": {
        "type": "parallel_agent",
        "model": MODEL_NAME,
        "description": "Silent background audit and risk detection",
        "system_prompt": """You are the Audit Workflow Agent for KRA Tax Assistant.

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
    }
}

# Workflow definitions
WORKFLOWS = {
    "IT1_FILING": {
        "steps": [
            "section_a_part1",  # Return info
            "section_a_part2",  # Bank details
            "section_a_part3",  # Auditor (conditional)
            "section_f",         # Employment income
            "section_f2",        # Other income (conditional)
            "section_h",         # Estate/trust (conditional)
            "section_j",         # Mortgage (conditional)
            "section_k",         # HOSP (conditional)
            "section_l",         # Insurance (conditional)
            "section_m",         # PAYE (auto-triggered)
            "section_n",         # Installment tax (conditional)
            "section_o",         # WHT (conditional)
            "section_p",         # Advance tax (conditional)
            "section_q",         # Income tax paid (conditional)
            "section_r",         # DTAA (conditional)
            "section_t"          # Tax computation (auto-compute)
        ],
        "conditional_triggers": {
            "section_a_part3": "is_audited == Yes",
            "section_a_part4": "has_rental_expense == True",
            "section_a_part5": "has_rental_income == True",
            "section_a_part6": "has_disability == Yes",
            "section_f2": "has_other_income == Yes",
            "section_h": "has_partnership_income == Yes",
            "section_j": "has_mortgage == Yes",
            "section_k": "has_hosp == Yes",
            "section_l": "has_insurance == Yes",
            "section_n": "paid_installment_tax == Yes",
            "section_o": "has_wht_credits == Yes",
            "section_p": "has_commercial_vehicle == Yes",
            "section_q": "paid_income_tax_advance == Yes",
            "section_r": "has_foreign_income == Yes"
        }
    },
    
    "VAT3_FILING": {
        "steps": [
            "section_a_info",
            "section_b_general_sales",
            "section_c_other_sales",
            "section_d_zero_rated",
            "section_e_exempt",
            "section_f_general_purchases",
            "section_g_other_purchases",
            "section_h_zero_rated_purchases",
            "section_i_exempt_purchases",
            "section_j_imported_services",
            "section_k_vat_paid",
            "section_l_wht",
            "section_m_sales_summary",    # Auto-compute
            "section_n_purchase_summary", # Auto-compute
            "section_o_calculation"       # Auto-compute
        ],
        "conditional_triggers": {
            "section_b_general_sales": "has_16_sales == Yes",
            "section_c_other_sales": "has_8_sales == Yes",
            "section_d_zero_rated": "has_zero_rated_sales == Yes",
            "section_e_exempt": "has_exempt_sales == Yes",
            "section_f_general_purchases": "has_16_purchases == Yes",
            "section_g_other_purchases": "has_8_purchases == Yes",
            "section_h_zero_rated_purchases": "has_zero_rated_purchases == Yes",
            "section_i_exempt_purchases": "has_exempt_purchases == Yes",
            "section_j_imported_services": "has_imported_services == Yes",
            "section_k_vat_paid": "paid_vat_advance == Yes",
            "section_l_wht": "has_wht_vat == Yes"
        }
    },
    
    "AUDIT_PIPELINE": {
        "parallel_tasks": [
            "fetch_bank_data",
            "fetch_mpesa_data",
            "fetch_vehicle_data",
            "fetch_property_data",
            "fetch_import_data",
            "fetch_telco_data"
        ],
        "sequential_tasks": [
            "build_wealth_profile",
            "financial_pattern_analysis",
            "asset_valuation",
            "luxury_goods_detection",
            "risk_scoring",
            "audit_case_creation"
        ]
    }
}

# Guardrail configurations
GUARDRAILS = {
    "input_validation": {
        "max_input_length": 500,
        "kra_pin_pattern": r'^A\d{9}P$',
        "date_pattern": r'^\d{4}-\d{2}-\d{2}$',
        "financial_max": 999999999999.99
    },
    
    "security": {
        "prompt_injection_detection": True,
        "audit_leak_prevention": True,
        "row_level_security": True,
        "access_logging": True
    },
    
    "data_access": {
        "roles": ["TAXPAYER", "OFFICER", "SYSTEM"],
        "taxpayer_can_access": ["own_filings", "own_session"],
        "officer_can_access": ["all_filings", "audit_cases"],
        "system_can_access": ["all_tables"]
    }
}

# Risk thresholds
RISK_THRESHOLDS = {
    "LOW": {"min": 0, "max": 30, "action": "NO_ACTION"},
    "MEDIUM": {"min": 31, "max": 60, "action": "CREATE_AUDIT_CASE"},
    "HIGH": {"min": 61, "max": 100, "action": "CREATE_AUDIT_CASE"}
}

# Tax computation constants
TAX_CONSTANTS = {
    "IT1": {
        "personal_relief": 28800,
        "insurance_relief_max": 60000,
        "hosp_max": 96000,
        "pension_exempt_threshold": 300000,
        "tax_bands": [
            {"min": 0, "max": 288000, "rate": 0.10},
            {"min": 288001, "max": 388000, "rate": 0.25},
            {"min": 388001, "max": float('inf'), "rate": 0.30}
        ]
    },
    "VAT3": {
        "standard_rate": 0.16,
        "reduced_rate": 0.08,
        "zero_rate": 0.00
    }
}

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get configuration for specific agent"""
    return AGENT_CONFIG.get(agent_name, {})

def get_workflow(workflow_name: str) -> Dict[str, Any]:
    """Get workflow definition"""
    return WORKFLOWS.get(workflow_name, {})

def get_guardrails() -> Dict[str, Any]:
    """Get guardrail configuration"""
    return GUARDRAILS

def get_risk_threshold(score: int) -> str:
    """Get risk level for given score"""
    for level, config in RISK_THRESHOLDS.items():
        if config['min'] <= score <= config['max']:
            return level
    return "UNKNOWN"

def get_tax_constants(filing_type: str) -> Dict[str, Any]:
    """Get tax computation constants"""
    return TAX_CONSTANTS.get(filing_type, {})
