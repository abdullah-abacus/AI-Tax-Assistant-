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

class VAT3FilingTools:
    """All VAT3 form section tools with exact questions as specified"""
    
    def section_a_info(self) -> Dict[str, Any]:
        """Return Information"""
        return {
            "section": "VAT_A",
            "questions": [
                {"id": "q1", "text": "What is your KRA PIN?", "field": "kra_pin"},
                {"id": "q2", "text": "Type of return? (Original/Amended)", "field": "return_type"},
                {"id": "q3", "text": "Entity type? (Head Office/Branch)", "field": "entity_type"},
                {"id": "q4", "text": "Return period from? (YYYY-MM-DD)", "field": "period_from"},
                {"id": "q5", "text": "Return period to? (YYYY-MM-DD)", "field": "period_to"},
                {"id": "q6", "text": "Are you non-resident with no fixed place in Kenya? (Yes/No)", "field": "non_resident"}
            ]
        }
    
    def section_b_general_sales(self) -> Dict[str, Any]:
        """Sales (General Rate 16%)"""
        return {
            "section": "VAT_B",
            "questions": [
                {"id": "q1", "text": "Do you have taxable sales at 16% rate? (Yes/No)", "field": "has_16_sales"}
            ],
            "conditional_questions": {
                "has_16_sales": {
                    "Yes": [
                        {"id": "q2", "text": "Total sales to VAT-registered customers (KES)?", "field": "sales_registered"},
                        {"id": "q3", "text": "Total sales to non-registered customers (KES)?", "field": "sales_non_registered"},
                        {"id": "q4", "text": "Taxable value (KES)?", "field": "taxable_value"}
                    ]
                }
            },
            "computation": "vat_16 = taxable_value × 0.16"
        }
    
    def section_c_other_sales(self) -> Dict[str, Any]:
        """Sales (Other Rate 8%)"""
        return {
            "section": "VAT_C",
            "questions": [
                {"id": "q1", "text": "Do you have taxable sales at 8% rate? (Yes/No)", "field": "has_8_sales"}
            ],
            "conditional_questions": {
                "has_8_sales": {
                    "Yes": [
                        {"id": "q2", "text": "Total sales to VAT-registered customers (KES)?", "field": "sales_registered"},
                        {"id": "q3", "text": "Total sales to non-registered customers (KES)?", "field": "sales_non_registered"},
                        {"id": "q4", "text": "Taxable value (KES)?", "field": "taxable_value"}
                    ]
                }
            },
            "computation": "vat_8 = taxable_value × 0.08"
        }
    
    def section_d_zero_rated(self) -> Dict[str, Any]:
        """Zero Rated Sales"""
        return {
            "section": "VAT_D",
            "questions": [
                {"id": "q1", "text": "Do you have zero-rated sales? (Yes/No)", "field": "has_zero_rated_sales"}
            ],
            "conditional_questions": {
                "has_zero_rated_sales": {
                    "Yes": [
                        {"id": "q2", "text": "Type of sales? (Category A/B/D/F)", "field": "category"},
                        {"id": "q3", "text": "Exemption certificate number? (if applicable)", "field": "exemption_cert"},
                        {"id": "q4", "text": "Taxable value for local/exemption (KES)?", "field": "local_value"},
                        {"id": "q5", "text": "Custom entry number? (for exports)", "field": "customs_entry"},
                        {"id": "q6", "text": "Port of exit? (for exports)", "field": "port_exit"},
                        {"id": "q7", "text": "Destination country? (for exports)", "field": "destination"},
                        {"id": "q8", "text": "Taxable value for exports (KES)?", "field": "export_value"}
                    ]
                }
            }
        }
    
    def section_e_exempt(self) -> Dict[str, Any]:
        """Exempt Sales"""
        return {
            "section": "VAT_E",
            "questions": [
                {"id": "q1", "text": "Do you have exempt sales? (Yes/No)", "field": "has_exempt_sales"}
            ],
            "conditional_questions": {
                "has_exempt_sales": {
                    "Yes": [
                        {"id": "q2", "text": "Sales value (KES)?", "field": "exempt_sales_value"}
                    ]
                }
            }
        }
    
    def section_f_general_purchases(self) -> Dict[str, Any]:
        """Purchases (General Rate 16%)"""
        return {
            "section": "VAT_F",
            "questions": [
                {"id": "q1", "text": "Do you have purchases at 16% rate? (Yes/No)", "field": "has_16_purchases"}
            ],
            "conditional_questions": {
                "has_16_purchases": {
                    "Yes": [
                        {"id": "q2", "text": "Total purchases from VAT-registered suppliers (local) (KES)?", "field": "local_purchases"},
                        {"id": "q3", "text": "Total purchases from imports (KES)?", "field": "import_purchases"},
                        {"id": "q4", "text": "Taxable value (KES)?", "field": "taxable_value"}
                    ]
                }
            },
            "computation": "input_vat_16 = taxable_value × 0.16"
        }
    
    def section_g_other_purchases(self) -> Dict[str, Any]:
        """Purchases (Other Rate 8%)"""
        return {
            "section": "VAT_G",
            "questions": [
                {"id": "q1", "text": "Do you have purchases at 8% rate? (Yes/No)", "field": "has_8_purchases"}
            ],
            "conditional_questions": {
                "has_8_purchases": {
                    "Yes": [
                        {"id": "q2", "text": "Total purchases from VAT-registered suppliers (KES)?", "field": "local_purchases"},
                        {"id": "q3", "text": "Total purchases from imports (KES)?", "field": "import_purchases"},
                        {"id": "q4", "text": "Taxable value (KES)?", "field": "taxable_value"}
                    ]
                }
            },
            "computation": "input_vat_8 = taxable_value × 0.08"
        }
    
    def section_h_zero_rated_purchases(self) -> Dict[str, Any]:
        """Zero Rated Purchases"""
        return {
            "section": "VAT_H",
            "questions": [
                {"id": "q1", "text": "Do you have zero-rated purchases? (Yes/No)", "field": "has_zero_rated_purchases"}
            ],
            "conditional_questions": {
                "has_zero_rated_purchases": {
                    "Yes": [
                        {"id": "q2", "text": "Total purchases from registered suppliers (KES)?", "field": "local_purchases"},
                        {"id": "q3", "text": "Total purchases from imports (KES)?", "field": "import_purchases"},
                        {"id": "q4", "text": "Taxable value (KES)?", "field": "taxable_value"}
                    ]
                }
            }
        }
    
    def section_i_exempt_purchases(self) -> Dict[str, Any]:
        """Exempt Purchases"""
        return {
            "section": "VAT_I",
            "questions": [
                {"id": "q1", "text": "Do you have exempt purchases? (Yes/No)", "field": "has_exempt_purchases"}
            ],
            "conditional_questions": {
                "has_exempt_purchases": {
                    "Yes": [
                        {"id": "q2", "text": "Total from registered suppliers (KES)?", "field": "registered_purchases"},
                        {"id": "q3", "text": "Total from imports (KES)?", "field": "import_purchases"},
                        {"id": "q4", "text": "Total where VAT not incurred (KES)?", "field": "no_vat_purchases"}
                    ]
                }
            }
        }
    
    def section_j_imported_services(self) -> Dict[str, Any]:
        """VAT on Imported Services"""
        return {
            "section": "VAT_J",
            "questions": [
                {"id": "q1", "text": "Do you import services from abroad? (Yes/No)", "field": "has_imported_services"}
            ],
            "conditional_questions": {
                "has_imported_services": {
                    "Yes": [
                        {"id": "q2", "text": "Name of supplier?", "field": "supplier_name"},
                        {"id": "q3", "text": "Description of services?", "field": "service_description"},
                        {"id": "q4", "text": "Transaction date? (YYYY-MM-DD)", "field": "transaction_date"},
                        {"id": "q5", "text": "Amount of VAT claimable (KES)?", "field": "vat_claimable"}
                    ]
                }
            }
        }
    
    def section_k_vat_paid(self) -> Dict[str, Any]:
        """VAT Paid in Advance"""
        return {
            "section": "VAT_K",
            "questions": [
                {"id": "q1", "text": "Did you pay VAT in advance? (Yes/No)", "field": "paid_vat_advance"}
            ],
            "conditional_questions": {
                "paid_vat_advance": {
                    "Yes": [
                        {"id": "q2", "text": "K1 - Advance Payment registration number?", "field": "advance_payment_reg"},
                        {"id": "q3", "text": "K1 - Date of deposit? (YYYY-MM-DD)", "field": "advance_payment_date"},
                        {"id": "q4", "text": "K1 - Amount (KES)?", "field": "advance_payment_amount"},
                        {"id": "q5", "text": "K2 - Self Assessment registration number?", "field": "self_assessment_reg"},
                        {"id": "q6", "text": "K2 - Date of deposit? (YYYY-MM-DD)", "field": "self_assessment_date"},
                        {"id": "q7", "text": "K2 - Amount (KES)?", "field": "self_assessment_amount"},
                        {"id": "q8", "text": "K3 - Credit Adjustment voucher/approval order number?", "field": "credit_adjustment_voucher"},
                        {"id": "q9", "text": "K3 - Date?", "field": "credit_adjustment_date"},
                        {"id": "q10", "text": "K3 - Amount (KES)?", "field": "credit_adjustment_amount"}
                    ]
                }
            }
        }
    
    def section_l_wht(self) -> Dict[str, Any]:
        """Withholding VAT Certificate"""
        return {
            "section": "VAT_L",
            "questions": [
                {"id": "q1", "text": "Do you have withholding VAT certificates? (Yes/No)", "field": "has_wht_vat"}
            ],
            "conditional_questions": {
                "has_wht_vat": {
                    "Yes": [
                        {"id": "q2", "text": "PIN of withholder?", "field": "withholder_pin"},
                        {"id": "q3", "text": "Name of withholder?", "field": "withholder_name"},
                        {"id": "q4", "text": "Certificate number?", "field": "certificate_number"},
                        {"id": "q5", "text": "Date of certificate? (YYYY-MM-DD)", "field": "certificate_date"},
                        {"id": "q6", "text": "Amount of VAT withheld (KES)?", "field": "vat_withheld"}
                    ]
                }
            }
        }
    
    def section_m_sales_summary(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sales Summary - AUTO COMPUTE, NO USER QUESTIONS"""
        vat_b_value = safe_float(collected_data.get('VAT_B', {}).get('taxable_value', 0))
        vat_c_value = safe_float(collected_data.get('VAT_C', {}).get('taxable_value', 0))
        vat_d_local = safe_float(collected_data.get('VAT_D', {}).get('local_value', 0))
        vat_d_export = safe_float(collected_data.get('VAT_D', {}).get('export_value', 0))
        vat_e_value = safe_float(collected_data.get('VAT_E', {}).get('exempt_sales_value', 0))
        
        taxable_sales = vat_b_value + vat_c_value
        zero_rated_sales = vat_d_local + vat_d_export
        exempt_sales = vat_e_value
        total_sales = taxable_sales + zero_rated_sales + exempt_sales
        
        output_vat_16 = vat_b_value * 0.16
        output_vat_8 = vat_c_value * 0.08
        total_output_vat = output_vat_16 + output_vat_8
        
        return {
            "section": "VAT_M",
            "summary": {
                "taxable_sales": taxable_sales,
                "zero_rated_sales": zero_rated_sales,
                "exempt_sales": exempt_sales,
                "total_sales": total_sales,
                "output_vat_16": output_vat_16,
                "output_vat_8": output_vat_8,
                "total_output_vat": total_output_vat
            }
        }
    
    def section_n_purchase_summary(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Purchase Summary - AUTO COMPUTE, NO USER QUESTIONS"""
        vat_f_value = safe_float(collected_data.get('VAT_F', {}).get('taxable_value', 0))
        vat_g_value = safe_float(collected_data.get('VAT_G', {}).get('taxable_value', 0))
        vat_h_value = safe_float(collected_data.get('VAT_H', {}).get('taxable_value', 0))
        vat_i_registered = safe_float(collected_data.get('VAT_I', {}).get('registered_purchases', 0))
        vat_i_import = safe_float(collected_data.get('VAT_I', {}).get('import_purchases', 0))
        vat_i_no_vat = safe_float(collected_data.get('VAT_I', {}).get('no_vat_purchases', 0))
        
        taxable_purchases = vat_f_value + vat_g_value
        zero_rated_purchases = vat_h_value
        exempt_purchases = vat_i_registered + vat_i_import + vat_i_no_vat
        total_purchases = taxable_purchases + zero_rated_purchases + exempt_purchases
        
        input_vat_16 = vat_f_value * 0.16
        input_vat_8 = vat_g_value * 0.08
        total_input_vat = input_vat_16 + input_vat_8
        
        return {
            "section": "VAT_N",
            "summary": {
                "taxable_purchases": taxable_purchases,
                "zero_rated_purchases": zero_rated_purchases,
                "exempt_purchases": exempt_purchases,
                "total_purchases": total_purchases,
                "input_vat_16": input_vat_16,
                "input_vat_8": input_vat_8,
                "total_input_vat": total_input_vat
            }
        }
    
    def section_o_calculation(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """VAT Due Calculation - AUTO COMPUTE, NO USER QUESTIONS"""
        sales_summary = self.section_m_sales_summary(collected_data)
        purchase_summary = self.section_n_purchase_summary(collected_data)
        
        output_vat = sales_summary['summary']['total_output_vat']
        input_vat = purchase_summary['summary']['total_input_vat']
        imported_services_vat = safe_float(collected_data.get('VAT_J', {}).get('vat_claimable', 0))
        
        total_sales = sales_summary['summary']['total_sales']
        exempt_sales = sales_summary['summary']['exempt_sales']
        
        if total_sales > 0:
            exempt_ratio = exempt_sales / total_sales
            non_deductible_input_vat = input_vat * exempt_ratio
        else:
            non_deductible_input_vat = 0
        
        deductible_input_vat = input_vat - non_deductible_input_vat + imported_services_vat
        
        vat_payable_credit = output_vat - deductible_input_vat
        
        credit_brought_forward = 0  # Could be from previous period
        
        wht_credits = safe_float(collected_data.get('VAT_L', {}).get('vat_withheld', 0))
        advance_payment = safe_float(collected_data.get('VAT_K', {}).get('advance_payment_amount', 0))
        self_assessment = safe_float(collected_data.get('VAT_K', {}).get('self_assessment_amount', 0))
        credit_adjustment = safe_float(collected_data.get('VAT_K', {}).get('credit_adjustment_amount', 0))
        
        vat_paid = advance_payment + self_assessment + credit_adjustment
        
        net_vat = vat_payable_credit + credit_brought_forward - wht_credits - vat_paid
        
        return {
            "section": "VAT_O",
            "calculation": {
                "output_vat": output_vat,
                "input_vat": input_vat,
                "imported_services_vat": imported_services_vat,
                "non_deductible_input_vat": non_deductible_input_vat,
                "deductible_input_vat": deductible_input_vat,
                "vat_payable_credit": vat_payable_credit,
                "credit_brought_forward": credit_brought_forward,
                "wht_credits": wht_credits,
                "vat_paid": vat_paid,
                "net_vat_payable_credit": net_vat,
                "status": "VAT_PAYABLE" if net_vat > 0 else "CREDIT_CARRIED_FORWARD"
            }
        }
