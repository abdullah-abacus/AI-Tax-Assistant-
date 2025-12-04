"""
Filing Workflow Agent using Google ADK Sequential Agent + Gemini 2.5 Pro
Guides users through step-by-step tax return filing
"""
import os
from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types
from typing import Dict, Any, Optional
from src.tools.filing.it1_tools import IT1FilingTools
from src.tools.filing.vat3_tools import VAT3FilingTools
from src.tools.guardrails.validation_tools import (
    validate_kra_pin,
    sanitize_financial_input,
    validate_date_input
)
from src.database.db_manager import save_filing_data
from src.agents.audit_workflow_agent import trigger_audit_workflow

FILING_INSTRUCTION = """You are the Filing Workflow Agent for KRA Tax Assistant.

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

def create_filing_agent():
    """Create ADK Sequential Filing Agent with Gemini 2.5 Pro"""
    
    # Configure Gemini model
    generate_config = types.GenerateContentConfig(
        temperature=0.1,  # Very low temperature for consistency
        max_output_tokens=1000,
        top_p=0.95
    )
    
    # Create LLM Agent for conversational filing
    filing_agent = LlmAgent(
        model="gemini-2.5-pro",
        name="filing_agent",
        instruction=FILING_INSTRUCTION,
        generate_content_config=generate_config
    )
    
    return filing_agent

class FilingWorkflowAgentADK:
    """Sequential workflow agent for tax filing using Google ADK"""
    
    def __init__(self):
        self.name = "filing_workflow_adk"
        self.it1_tools = IT1FilingTools()
        self.vat3_tools = VAT3FilingTools()
        self.gemini_agent = create_filing_agent()
    
    def get_next_question(self, section_name: str, section_data: Dict[str, Any], collected_responses: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get next unanswered question from section"""
        questions = section_data.get('questions', [])
        
        for question in questions:
            field = question['field']
            if field not in collected_responses:
                return question
        
        conditional_questions = section_data.get('conditional_questions', {})
        for condition_field, conditions in conditional_questions.items():
            if condition_field in collected_responses:
                condition_value = collected_responses[condition_field]
                if condition_value in conditions:
                    for question in conditions[condition_value]:
                        field = question['field']
                        if field not in collected_responses:
                            return question
        
        return None
    
    def validate_response(self, field_name: str, response: str) -> Dict[str, Any]:
        """Validate user response based on field type"""
        name = field_name.lower()

        # PIN fields (except main KRA PIN) – accept as-is
        if 'pin' in name and field_name != 'kra_pin':
            return {"valid": True, "value": response}

        # Main KRA PIN format validation
        if field_name == 'kra_pin':
            return validate_kra_pin(response)

        # Yes/No flags (booleans) – don't treat them as amounts even if they mention "income"
        if name.startswith(('has_', 'is_', 'paid_', 'declare_', 'do_you_', 'did_you_')):
            return {"valid": True, "value": response}

        # Monetary / numeric amounts
        if any(keyword in name for keyword in ['amount', 'pay', 'income', 'value', 'paid', 'relief', 'deposit']):
            return sanitize_financial_input(response)

        # Dates and period ranges
        if 'date' in name or 'from' in name or 'to' in name:
            return validate_date_input(response)

        # Default: accept as plain text
        return {"valid": True, "value": response}
    
    def process_section_a_part1(self, session_id: str) -> Dict[str, Any]:
        """Process Section A Part 1 - Return Information"""
        section_data = self.it1_tools.section_a_part1()
        return {
            "section": "A_PART1",
            "data": section_data,
            "message": "Let's start filing your IT1 return. I'll ask you 12 questions about your return information."
        }

    def process_section_a_part2(self, session_id: str) -> Dict[str, Any]:
        """Process Section A Part 2 - Bank Details"""
        section_data = self.it1_tools.section_a_part2()
        return {
            "section": "A_PART2",
            "data": section_data,
            "message": "Now let's capture your bank account details for refund or payment purposes."
        }

    def process_section_a_part3(self, session_id: str) -> Dict[str, Any]:
        """Process Section A Part 3 - Auditor Details (conditional inside section)"""
        section_data = self.it1_tools.section_a_part3()
        return {
            "section": "A_PART3",
            "data": section_data,
            "message": "Next, please confirm whether this return is audited. If yes, I'll ask for your auditor details."
        }

    def process_section_a_part6(self, session_id: str) -> Dict[str, Any]:
        """Process Section A Part 6 - Disability Exemption (conditional inside section)"""
        section_data = self.it1_tools.section_a_part6()
        return {
            "section": "A_PART6",
            "data": section_data,
            "message": "Now let's capture your disability exemption certificate details."
        }
    
    def process_section_f(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section F - Employment Income"""
        section_data = self.it1_tools.section_f_employment_income()
        return {
            "section": "F",
            "data": section_data,
            "message": "Now let's collect your employment income information."
        }

    def process_section_f2_other_income(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section F2 - Other Income Types (lumpsum, gratuity, dividends, etc.)"""
        section_data = self.it1_tools.section_f2_other_income()
        return {
            "section": "F2",
            "data": section_data,
            "message": "Now let's check if you have any other income such as lumpsum, gratuity, pension arrears, or dividends."
        }

    def process_section_h_estate_trust(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section H - Estate / Trust Income"""
        section_data = self.it1_tools.section_h_estate_trust()
        return {
            "section": "H",
            "data": section_data,
            "message": "Now let's check if you receive any income from an estate, trust, or settlement."
        }
    
    def process_section_j_mortgage(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section J - Mortgage Interest (triggered if has_mortgage == Yes)"""
        section_data = self.it1_tools.section_j_mortgage()
        return {
            "section": "J",
            "data": section_data,
            "message": "Now let's collect your mortgage interest information."
        }
    
    def process_section_l_insurance(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section L - Insurance Relief (triggered if has_insurance == Yes)"""
        section_data = self.it1_tools.section_l_insurance()
        return {
            "section": "L",
            "data": section_data,
            "message": "Now let's collect your insurance policy information."
        }
    
    def process_section_r_dtaa(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section R - DTAA Credits (triggered if has_foreign_income == Yes)"""
        section_data = self.it1_tools.section_r_dtaa()
        return {
            "section": "R",
            "data": section_data,
            "message": "Now let's collect your foreign income and DTAA information."
        }

    def process_section_k_hosp(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section K - Home Ownership Savings Plan"""
        section_data = self.it1_tools.section_k_hosp()
        return {
            "section": "K",
            "data": section_data,
            "message": "Now let's capture any Home Ownership Savings Plan (HOSP) contributions you made."
        }

    def process_section_m_paye(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section M - PAYE Deducted at Source"""
        section_data = self.it1_tools.section_m_paye()
        return {
            "section": "M",
            "data": section_data,
            "message": "Now let's capture PAYE details from your employment."
        }

    def process_section_n_installment_tax(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section N - Installment Tax Credits"""
        section_data = self.it1_tools.section_n_installment_tax()
        return {
            "section": "N",
            "data": section_data,
            "message": "Now let's record any installment tax payments you may have made."
        }

    def process_section_o_wht(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section O - Withholding Tax Credits"""
        section_data = self.it1_tools.section_o_wht()
        return {
            "section": "O",
            "data": section_data,
            "message": "Now let's capture any withholding tax (WHT) credits you have."
        }

    def process_section_p_advance_tax(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section P - Advance Tax on Commercial Vehicle"""
        section_data = self.it1_tools.section_p_advance_tax()
        return {
            "section": "P",
            "data": section_data,
            "message": "Now let's capture any advance tax paid on commercial vehicles."
        }

    def process_section_q_income_tax_paid(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Section Q - Income Tax Paid in Advance"""
        section_data = self.it1_tools.section_q_income_tax_paid()
        return {
            "section": "Q",
            "data": section_data,
            "message": "Finally, let's capture any income tax you paid in advance."
        }
    
    def compute_final_tax(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute final tax using Section T"""
        computation = self.it1_tools.section_t_tax_computation(collected_data)
        return computation
    
    # ===== VAT3 WORKFLOW HELPERS =====
    def process_vat3_section_a(self, session_id: str) -> Dict[str, Any]:
        """Process VAT3 Section A - Return Information"""
        section_data = self.vat3_tools.section_a_info()
        return {
            "section": "VAT_A",
            "data": section_data,
            "message": "Let's start filing your VAT3 return. I'll first collect your basic return information."
        }

    def process_vat3_section_b(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section B - General rated sales (16%)"""
        section_data = self.vat3_tools.section_b_general_sales()
        return {
            "section": "VAT_B",
            "data": section_data,
            "message": "Now let's capture your taxable sales at the 16% VAT rate."
        }

    def process_vat3_section_c(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section C - Sales at 8% rate"""
        section_data = self.vat3_tools.section_c_other_sales()
        return {
            "section": "VAT_C",
            "data": section_data,
            "message": "Now let's capture your taxable sales at the 8% VAT rate."
        }

    def process_vat3_section_d(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section D - Zero-rated sales"""
        section_data = self.vat3_tools.section_d_zero_rated()
        return {
            "section": "VAT_D",
            "data": section_data,
            "message": "Now let's capture your zero-rated sales information."
        }

    def process_vat3_section_e(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section E - Exempt sales"""
        section_data = self.vat3_tools.section_e_exempt()
        return {
            "section": "VAT_E",
            "data": section_data,
            "message": "Now let's capture your exempt sales information."
        }

    def process_vat3_section_f(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section F - General rated purchases (16%)"""
        section_data = self.vat3_tools.section_f_general_purchases()
        return {
            "section": "VAT_F",
            "data": section_data,
            "message": "Now let's capture your purchases at the 16% VAT rate."
        }

    def process_vat3_section_g(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section G - Purchases at 8% rate"""
        section_data = self.vat3_tools.section_g_other_purchases()
        return {
            "section": "VAT_G",
            "data": section_data,
            "message": "Now let's capture your purchases at the 8% VAT rate."
        }

    def process_vat3_section_h(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section H - Zero-rated purchases"""
        section_data = self.vat3_tools.section_h_zero_rated_purchases()
        return {
            "section": "VAT_H",
            "data": section_data,
            "message": "Now let's capture your zero-rated purchases information."
        }

    def process_vat3_section_i(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section I - Exempt purchases"""
        section_data = self.vat3_tools.section_i_exempt_purchases()
        return {
            "section": "VAT_I",
            "data": section_data,
            "message": "Now let's capture your exempt purchases information."
        }

    def process_vat3_section_j(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section J - Imported services"""
        section_data = self.vat3_tools.section_j_imported_services()
        return {
            "section": "VAT_J",
            "data": section_data,
            "message": "Now let's capture your imported services information."
        }

    def process_vat3_section_k(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section K - VAT paid in advance"""
        section_data = self.vat3_tools.section_k_vat_paid()
        return {
            "section": "VAT_K",
            "data": section_data,
            "message": "Now let's capture your VAT paid in advance information."
        }

    def process_vat3_section_l(self, session_id: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VAT3 Section L - Withholding VAT certificates"""
        section_data = self.vat3_tools.section_l_wht()
        return {
            "section": "VAT_L",
            "data": section_data,
            "message": "Now let's capture your withholding VAT certificates information."
        }

    def compute_vat3(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute VAT3 totals using Section O calculation"""
        calculation = self.vat3_tools.section_o_calculation(collected_data)
        return calculation
    
    def trigger_background_audit(self, kra_pin: str, declared_income: float):
        """Trigger silent background audit - results NOT returned to user"""
        trigger_audit_workflow(kra_pin, declared_income)
    
    def save_response(self, kra_pin: str, filing_type: str, section: str, field_name: str, field_value: str, session_id: str):
        """Save filing response to database"""
        save_filing_data(kra_pin, filing_type, section, field_name, field_value, session_id)
    
    def ask_question_with_gemini(self, question: str, user_id: str) -> str:
        """
        Use Gemini to generate natural, conversational question
        
        Args:
            question: Form question text
            user_id: User identifier
            
        Returns:
            Natural language question from Gemini
        """
        try:
            prompt = f"Rephrase this tax form question in a friendly, conversational way (keep it concise): {question}"
            response = self.gemini_agent.query(
                user_id=user_id,
                message=prompt
            )
            return response.content
        except:
            # Fallback to original question
            return question
