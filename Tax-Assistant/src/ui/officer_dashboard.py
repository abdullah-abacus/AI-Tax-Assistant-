from src.database.db_manager import get_all_audit_cases, get_filings_by_pin

def display_dashboard():
    """Display officer dashboard with audit cases"""
    cases = get_all_audit_cases()
    
    print("\n" + "="*80)
    print("KRA OFFICER DASHBOARD - AUDIT CASES")
    print("="*80 + "\n")
    
    if not cases:
        print("No audit cases found.")
        return
    
    for case in cases:
        print(f"{'='*80}")
        print(f"CASE ID: {case['id']}")
        print(f"KRA PIN: {case['kra_pin']}")
        print(f"RISK LEVEL: {case['risk_level']} (Score: {case['risk_score']}/100)")
        print(f"Status: {case['status']}")
        print(f"Created: {case['created_at']}")
        print(f"\n📊 FINANCIAL ANALYSIS:")
        print(f"  Declared Income: KES {case['declared_income']:,.2f}")
        print(f"  Inferred Income: KES {case['inferred_income']:,.2f}")
        print(f"  Discrepancy: KES {case['discrepancy_amount']:,.2f}")
        print(f"\n🔍 REASON:")
        print(f"  {case['reason']}")
        print(f"{'='*80}\n")

def view_case_details(kra_pin: str):
    """View detailed filing information for a specific case"""
    filings = get_filings_by_pin(kra_pin)
    
    print(f"\n{'='*80}")
    print(f"FILING DETAILS FOR PIN: {kra_pin}")
    print(f"{'='*80}\n")
    
    if not filings:
        print("No filing data found.")
        return
    
    current_section = None
    for filing in filings:
        if filing['section'] != current_section:
            current_section = filing['section']
            print(f"\n[Section {current_section}]")
        print(f"  {filing['field_name']}: {filing['field_value']}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    print("\n🚨 KRA OFFICER DASHBOARD")
    print("This dashboard is for KRA officers only.\n")
    
    display_dashboard()
    
    print("\nTo view case details, use: view_case_details('A001234567P')")
