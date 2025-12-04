from typing import Dict, Any, List

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float, handling strings like 'No', 'Yes', empty strings, etc."""
    if value is None:
        return default
    
    # If already a number, return it
    if isinstance(value, (int, float)):
        return float(value)
    
    # If it's a string, check if it's a boolean-like answer
    if isinstance(value, str):
        value = value.strip()
        # Handle Yes/No answers
        if value.lower() in ['no', 'yes', '', 'n', 'y']:
            return default
        # Try to convert to float
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    return default

class IT1FilingTools:
    """All IT1 form section tools with exact questions as specified"""
    
    def section_a_part1(self) -> Dict[str, Any]:
        """Return Information - 12 questions"""
        return {
            "section": "A_PART1",
            "questions": [
                {"id": "q1", "text": "What is your KRA PIN?", "field": "kra_pin"},
                {"id": "q2", "text": "Type of return? (Original/Amended)", "field": "return_type"},
                {"id": "q3", "text": "Return period from? (YYYY-MM-DD)", "field": "period_from"},
                {"id": "q4", "text": "Return period to? (YYYY-MM-DD)", "field": "period_to"},
                {"id": "q5", "text": "Do you have income other than employment? (Yes/No)", "field": "has_other_income"},
                {"id": "q6", "text": "Do you have partnership income? (Yes/No)", "field": "has_partnership_income"},
                {"id": "q7", "text": "Has employer provided car? (Yes/No)", "field": "has_car_benefit"},
                {"id": "q8", "text": "Do you have a mortgage? (Yes/No)", "field": "has_mortgage"},
                {"id": "q9", "text": "Do you have insurance policy? (Yes/No)", "field": "has_insurance"},
                {"id": "q10", "text": "Do you earn foreign income? (Yes/No)", "field": "has_foreign_income"},
                {"id": "q11", "text": "Do you have disability exemption certificate? (Yes/No)", "field": "has_disability"},
                {"id": "q12", "text": "Do you want to declare spouse's income? (Yes/No)", "field": "declare_spouse_income"}
            ]
        }
    
    def section_a_part2(self) -> Dict[str, Any]:
        """Bank Details - 5 questions"""
        return {
            "section": "A_PART2",
            "questions": [
                {"id": "q1", "text": "Bank name?", "field": "bank_name"},
                {"id": "q2", "text": "Branch name?", "field": "branch_name"},
                {"id": "q3", "text": "City?", "field": "city"},
                {"id": "q4", "text": "Account holder's name?", "field": "account_holder_name"},
                {"id": "q5", "text": "Account number?", "field": "account_number"}
            ]
        }
    
    def section_a_part3(self) -> Dict[str, Any]:
        """Auditor Details - conditional"""
        return {
            "section": "A_PART3",
            "questions": [
                {"id": "q1", "text": "Is this return audited? (Yes/No)", "field": "is_audited"}
            ],
            "conditional_questions": {
                "is_audited": {
                    "Yes": [
                        {"id": "q2", "text": "PIN of auditor?", "field": "auditor_pin"},
                        {"id": "q3", "text": "Name of auditor?", "field": "auditor_name"},
                        {"id": "q4", "text": "Date of audit certificate? (YYYY-MM-DD)", "field": "audit_date"}
                    ]
                }
            }
        }
    
    def section_a_part4(self) -> Dict[str, Any]:
        """Landlord Details - conditional on rental expense"""
        return {
            "section": "A_PART4",
            "trigger_condition": "has_rental_expense",
            "questions": [
                {"id": "q1", "text": "PIN of landlord (if available)?", "field": "landlord_pin"},
                {"id": "q2", "text": "Name of landlord?", "field": "landlord_name"},
                {"id": "q3", "text": "LR Number?", "field": "lr_number"},
                {"id": "q4", "text": "Building name?", "field": "building_name"},
                {"id": "q5", "text": "Street/Road?", "field": "street"},
                {"id": "q6", "text": "City/Town?", "field": "city"},
                {"id": "q7", "text": "County?", "field": "county"},
                {"id": "q8", "text": "District?", "field": "district"},
                {"id": "q9", "text": "Postal address?", "field": "postal_address"},
                {"id": "q10", "text": "Period of occupancy from? (YYYY-MM-DD)", "field": "occupancy_from"},
                {"id": "q11", "text": "Period of occupancy to? (YYYY-MM-DD)", "field": "occupancy_to"},
                {"id": "q12", "text": "Amount of gross rent paid (KES)?", "field": "rent_paid"}
            ]
        }
    
    def section_a_part5(self) -> Dict[str, Any]:
        """Tenant Details - conditional on rental income"""
        return {
            "section": "A_PART5",
            "trigger_condition": "has_rental_income",
            "questions": [
                {"id": "q1", "text": "PIN of tenant (if available)?", "field": "tenant_pin"},
                {"id": "q2", "text": "Name of tenant?", "field": "tenant_name"},
                {"id": "q3", "text": "Property LR Number?", "field": "property_lr_number"},
                {"id": "q4", "text": "Building name?", "field": "building_name"},
                {"id": "q5", "text": "Street/Road?", "field": "street"},
                {"id": "q6", "text": "City/Town?", "field": "city"},
                {"id": "q7", "text": "County?", "field": "county"},
                {"id": "q8", "text": "District?", "field": "district"},
                {"id": "q9", "text": "Postal address?", "field": "postal_address"},
                {"id": "q10", "text": "Period of occupancy from? (YYYY-MM-DD)", "field": "occupancy_from"},
                {"id": "q11", "text": "Period of occupancy to? (YYYY-MM-DD)", "field": "occupancy_to"},
                {"id": "q12", "text": "Amount of gross rental income (KES)?", "field": "rental_income"}
            ]
        }
    
    def section_a_part6(self) -> Dict[str, Any]:
        """Disability Exemption Certificate - conditional"""
        return {
            "section": "A_PART6",
            "trigger_condition": "has_disability",
            "questions": [
                {"id": "q1", "text": "Exemption certificate number?", "field": "certificate_number"},
                {"id": "q2", "text": "Valid from date? (YYYY-MM-DD)", "field": "valid_from"},
                {"id": "q3", "text": "Valid to date? (YYYY-MM-DD)", "field": "valid_to"}
            ]
        }
    
    def section_f_employment_income(self) -> Dict[str, Any]:
        """Employment Income - conditional"""
        return {
            "section": "F",
            "questions": [
                {"id": "q1", "text": "Do you have employment income? (Yes/No)", "field": "has_employment_income"}
            ],
            "conditional_questions": {
                "has_employment_income": {
                    "Yes": [
                        {"id": "q2", "text": "PIN of employer?", "field": "employer_pin"},
                        {"id": "q3", "text": "Name of employer?", "field": "employer_name"},
                        {"id": "q4", "text": "Gross pay (KES)?", "field": "gross_pay"},
                        {"id": "q5", "text": "Allowances and benefits (excluding car/housing) (KES)?", "field": "allowances"},
                        {"id": "q6", "text": "Value of car benefit (KES)?", "field": "car_benefit_value"},
                        {"id": "q7", "text": "Net value of housing (KES)?", "field": "housing_value"},
                        {"id": "q8", "text": "Pension if in excess of 300,000 (KES)?", "field": "pension_excess"}
                    ]
                }
            }
        }
    
    def section_f2_other_income(self) -> Dict[str, Any]:
        """Lumpsum/Gratuity/Pension/Arrears/Dividends"""
        return {
            "section": "F2",
            "questions": [
                {"id": "q1", "text": "Do you have any of these? (Lumpsum/Gratuity/Pension/Arrears/Qualifying Interest/Dividends/Others) (Yes/No)", "field": "has_other_income_types"}
            ],
            "conditional_questions": {
                "has_other_income_types": {
                    "Yes": [
                        {"id": "q2", "text": "Gross amount (KES)?", "field": "gross_amount"},
                        {"id": "q3", "text": "Tax deducted (KES)?", "field": "tax_deducted"}
                    ]
                }
            }
        }
    
    def section_h_estate_trust(self) -> Dict[str, Any]:
        """Estate/Trust Income"""
        return {
            "section": "H",
            "questions": [
                {"id": "q1", "text": "Do you receive income from estate/trust/settlement? (Yes/No)", "field": "has_estate_income"}
            ],
            "conditional_questions": {
                "has_estate_income": {
                    "Yes": [
                        {"id": "q2", "text": "Amount of share of income (KES)?", "field": "estate_income_amount"}
                    ]
                }
            }
        }
    
    def section_j_mortgage(self) -> Dict[str, Any]:
        """Mortgage Interest Computation"""
        return {
            "section": "J",
            "trigger_condition": "has_mortgage",
            "questions": [
                {"id": "q1", "text": "Lender name?", "field": "lender_name"},
                {"id": "q2", "text": "Amount of interest paid during year (KES)?", "field": "interest_paid"}
            ]
        }
    
    def section_k_hosp(self) -> Dict[str, Any]:
        """Home Ownership Savings Plan"""
        return {
            "section": "K",
            "questions": [
                {"id": "q1", "text": "Do you have HOSP? (Yes/No)", "field": "has_hosp"}
            ],
            "conditional_questions": {
                "has_hosp": {
                    "Yes": [
                        {"id": "q2", "text": "Name of HOSP institution?", "field": "hosp_institution"},
                        {"id": "q3", "text": "Total deposit for the year (KES)? (Max 96,000)", "field": "hosp_deposit"}
                    ]
                }
            }
        }
    
    def section_l_insurance(self) -> Dict[str, Any]:
        """Insurance Relief"""
        return {
            "section": "L",
            "trigger_condition": "has_insurance",
            "questions": [
                {"id": "q1", "text": "Insurance company name?", "field": "insurance_company"},
                {"id": "q2", "text": "Premium paid (KES)?", "field": "premium_paid"},
                {"id": "q3", "text": "Amount of insurance relief? (Max 60,000)", "field": "insurance_relief"}
            ]
        }
    
    def section_m_paye(self) -> Dict[str, Any]:
        """PAYE Deducted at Source"""
        return {
            "section": "M",
            "trigger_condition": "has_employment_income",
            "questions": [
                {"id": "q1", "text": "PIN of employer?", "field": "employer_pin"},
                {"id": "q2", "text": "Name of employer?", "field": "employer_name"},
                {"id": "q3", "text": "Taxable salary (KES)?", "field": "taxable_salary"},
                {"id": "q4", "text": "Tax payable on taxable salary (KES)?", "field": "tax_payable"},
                {"id": "q5", "text": "Amount of PAYE deducted (KES)?", "field": "paye_deducted"}
            ]
        }
    
    def section_n_installment_tax(self) -> Dict[str, Any]:
        """Installment Tax Credits"""
        return {
            "section": "N",
            "questions": [
                {"id": "q1", "text": "Did you pay installment tax? (Yes/No)", "field": "paid_installment_tax"}
            ],
            "conditional_questions": {
                "paid_installment_tax": {
                    "Yes": [
                        {"id": "q2", "text": "Payment registration number?", "field": "payment_reg_number"},
                        {"id": "q3", "text": "Date of payment? (YYYY-MM-DD)", "field": "payment_date"},
                        {"id": "q4", "text": "Amount paid (KES)?", "field": "amount_paid"}
                    ]
                }
            }
        }
    
    def section_o_wht(self) -> Dict[str, Any]:
        """Withholding Tax Credits"""
        return {
            "section": "O",
            "questions": [
                {"id": "q1", "text": "Do you have withholding tax credits? (Yes/No)", "field": "has_wht_credits"}
            ],
            "conditional_questions": {
                "has_wht_credits": {
                    "Yes": [
                        {"id": "q2", "text": "PIN of withholder?", "field": "withholder_pin"},
                        {"id": "q3", "text": "Name of withholder?", "field": "withholder_name"},
                        {"id": "q4", "text": "WHT certificate number?", "field": "wht_cert_number"},
                        {"id": "q5", "text": "Date of certificate? (YYYY-MM-DD)", "field": "cert_date"},
                        {"id": "q6", "text": "Amount of WHT (KES)?", "field": "wht_amount"}
                    ]
                }
            }
        }
    
    def section_p_advance_tax(self) -> Dict[str, Any]:
        """Advance Tax on Commercial Vehicle"""
        return {
            "section": "P",
            "questions": [
                {"id": "q1", "text": "Do you have commercial vehicle? (Yes/No)", "field": "has_commercial_vehicle"}
            ],
            "conditional_questions": {
                "has_commercial_vehicle": {
                    "Yes": [
                        {"id": "q2", "text": "Vehicle registration number?", "field": "vehicle_reg_number"},
                        {"id": "q3", "text": "Amount of advance tax paid (KES)?", "field": "advance_tax_paid"},
                        {"id": "q4", "text": "Payment date? (YYYY-MM-DD)", "field": "payment_date"}
                    ]
                }
            }
        }
    
    def section_q_income_tax_paid(self) -> Dict[str, Any]:
        """Income Tax Paid in Advance"""
        return {
            "section": "Q",
            "questions": [
                {"id": "q1", "text": "Did you pay income tax in advance? (Yes/No)", "field": "paid_income_tax_advance"}
            ],
            "conditional_questions": {
                "paid_income_tax_advance": {
                    "Yes": [
                        {"id": "q2", "text": "Payment registration number?", "field": "payment_reg_number"},
                        {"id": "q3", "text": "Date of deposit? (YYYY-MM-DD)", "field": "deposit_date"},
                        {"id": "q4", "text": "Amount paid (KES)?", "field": "amount_paid"}
                    ]
                }
            }
        }
    
    def section_r_dtaa(self) -> Dict[str, Any]:
        """Double Taxation Agreement Credits"""
        return {
            "section": "R",
            "trigger_condition": "has_foreign_income",
            "questions": [
                {"id": "q1", "text": "Country of foreign income?", "field": "foreign_country"},
                {"id": "q2", "text": "Amount of tax relief under DTAA (KES)?", "field": "dtaa_relief_amount"}
            ]
        }
    
    def section_t_tax_computation(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Final Tax Computation - AUTO COMPUTE, NO USER QUESTIONS"""
        total_income = 0.0
        
        # Employment Income (Section F) - Include ALL components
        section_f = collected_data.get('F', {})
        total_income += safe_float(section_f.get('gross_pay', 0))
        total_income += safe_float(section_f.get('allowances', 0))  # Allowances & benefits
        total_income += safe_float(section_f.get('car_benefit_value', 0))  # Car benefit
        total_income += safe_float(section_f.get('housing_value', 0))  # Net housing benefit
        
        # Other Income Sources
        total_income += safe_float(collected_data.get('F2', {}).get('gross_amount', 0))  # Lumpsum/Gratuity/etc
        total_income += safe_float(collected_data.get('H', {}).get('estate_income_amount', 0))  # Estate/Trust income
        
        pension_deduction = safe_float(collected_data.get('F', {}).get('pension_excess', 0))
        mortgage_interest = safe_float(collected_data.get('J', {}).get('interest_paid', 0))
        hosp_deposit = min(safe_float(collected_data.get('K', {}).get('hosp_deposit', 0)), 96000)
        
        relief_deduction = max(mortgage_interest, hosp_deposit)
        
        taxable_income = total_income - pension_deduction - relief_deduction
        
        tax_payable = 0.0
        if taxable_income <= 288000:
            tax_payable = taxable_income * 0.10
        elif taxable_income <= 388000:
            tax_payable = 288000 * 0.10 + (taxable_income - 288000) * 0.25
        else:
            tax_payable = 288000 * 0.10 + 100000 * 0.25 + (taxable_income - 388000) * 0.30
        
        personal_relief = 28800
        insurance_relief = min(safe_float(collected_data.get('L', {}).get('insurance_relief', 0)), 60000)
        
        tax_after_reliefs = max(tax_payable - personal_relief - insurance_relief, 0)
        
        total_credits = 0.0
        total_credits += safe_float(collected_data.get('M', {}).get('paye_deducted', 0))
        total_credits += safe_float(collected_data.get('N', {}).get('amount_paid', 0))
        total_credits += safe_float(collected_data.get('O', {}).get('wht_amount', 0))
        total_credits += safe_float(collected_data.get('P', {}).get('advance_tax_paid', 0))
        total_credits += safe_float(collected_data.get('Q', {}).get('amount_paid', 0))
        total_credits += safe_float(collected_data.get('R', {}).get('dtaa_relief_amount', 0))
        
        final_amount = tax_after_reliefs - total_credits
        
        return {
            "section": "T",
            "computation": {
                "total_income": total_income,
                "taxable_income": taxable_income,
                "tax_payable": tax_payable,
                "tax_after_reliefs": tax_after_reliefs,
                "total_credits": total_credits,
                "final_tax_due_or_refund": final_amount,
                "status": "TAX_DUE" if final_amount > 0 else "REFUND_DUE"
            }
        }
