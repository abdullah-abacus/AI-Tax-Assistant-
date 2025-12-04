"""
Admin/Officer Dashboard - Chainlit Web Interface
For KRA officers to view and manage audit cases
"""
import chainlit as cl
from src.database.db_manager import (
    get_all_audit_cases,
    get_filings_by_pin,
    get_bank_transactions,
    get_mpesa_transactions,
    get_vehicle_assets,
    get_property_assets,
    get_import_records,
    get_telco_usage
)

@cl.on_chat_start
async def start():
    """Initialize admin dashboard session"""
    await cl.Message(
        content="""# 🚨 KRA Officer Admin Dashboard

Welcome to the KRA Tax Assistant Admin Interface.

**Available Commands:**
- `show cases` - View HIGH risk audit cases only
- `search PIN` - Search by KRA PIN (e.g., `search A001234567P`)
- `details PIN` - View detailed filing information (e.g., `details A001234567P`)
- `help` - Show this help message

**Important:** 
- ⚠️ Only **HIGH RISK** cases are displayed (created after tax filing)
- 🔴 Cases appear automatically when significant discrepancies are detected
- 📊 This interface is for authorized KRA officers only
"""
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle admin commands"""
    user_input = message.content.strip().lower()
    
    if user_input == "show cases" or user_input == "cases":
        await show_all_cases()
    elif user_input.startswith("search "):
        pin = user_input.replace("search ", "").strip().upper()
        await search_by_pin(pin)
    elif user_input.startswith("details ") or user_input.startswith("detail "):
        pin = user_input.replace("details ", "").replace("detail ", "").strip().upper()
        await show_case_details(pin)
    elif user_input == "help":
        await show_help()
    else:
        await cl.Message(
            content="❌ Unknown command. Type `help` for available commands."
        ).send()

async def show_all_cases():
    """Display only HIGH risk audit cases (created after tax filing)"""
    all_cases = get_all_audit_cases()
    
    # Filter to ONLY HIGH risk cases
    high_risk_cases = [c for c in all_cases if c['risk_level'] == 'HIGH']
    
    if not high_risk_cases:
        await cl.Message(
            content="📭 No HIGH risk audit cases found.\n\n**Note:** Only HIGH risk cases (created after tax filing) are displayed in this dashboard."
        ).send()
        return
    
    summary = f"""# 🔴 HIGH RISK AUDIT CASES

**Total HIGH Risk Cases:** {len(high_risk_cases)}

**Note:** Only HIGH risk cases are shown here. These cases are automatically created after taxpayers file their returns when significant discrepancies are detected.

---
"""
    await cl.Message(content=summary).send()
    
    # Show only HIGH risk cases
    for case in high_risk_cases:
        await display_case_card(case)

async def display_case_card(case: dict):
    """Display a single audit case as a card"""
    risk_emoji = {
        'HIGH': '🔴',
        'MEDIUM': '🟡',
        'LOW': '🟢'
    }.get(case['risk_level'], '⚪')
    
    status_emoji = {
        'OPEN': '📂',
        'IN_REVIEW': '👀',
        'RESOLVED': '✅',
        'CLOSED': '🔒'
    }.get(case['status'], '📋')
    
    card_content = f"""### {risk_emoji} Case #{case['id']} - {case['kra_pin']}

**Risk Level:** {case['risk_level']} (Score: {case['risk_score']}/100)  
**Status:** {status_emoji} {case['status']}  
**Created:** {case['created_at']}

**Financial Analysis:**
- 💰 Declared Income: KES {case['declared_income']:,.2f}
- 📈 Inferred Income: KES {case['inferred_income']:,.2f}
- ⚠️ Discrepancy: KES {case['discrepancy_amount']:,.2f}

**Reason:** {case['reason']}

---
"""
    await cl.Message(content=card_content).send()

async def search_by_pin(pin: str):
    """Search for HIGH risk cases and filings by KRA PIN"""
    if not pin or len(pin) != 11 or not pin.startswith('A') or not pin.endswith('P'):
        await cl.Message(content="❌ Invalid KRA PIN format. Expected: A#########P").send()
        return
    
    # Get only HIGH risk audit cases for this PIN
    all_cases = get_all_audit_cases()
    high_risk_cases = [c for c in all_cases if c['kra_pin'] == pin and c['risk_level'] == 'HIGH']
    
    # Get filings for this PIN
    filings = get_filings_by_pin(pin)
    
    if not high_risk_cases and not filings:
        await cl.Message(
            content=f"📭 No HIGH risk cases or filing data found for PIN: {pin}\n\n**Note:** Only HIGH risk cases are displayed."
        ).send()
        return
    
    result = f"""# 🔍 Search Results for PIN: {pin}

"""
    
    if high_risk_cases:
        result += f"**HIGH Risk Audit Cases Found:** {len(high_risk_cases)}\n\n"
        for case in high_risk_cases:
            result += f"- Case #{case['id']}: 🔴 HIGH Risk (Score: {case['risk_score']}/100) - {case['status']}\n"
        result += "\n"
    else:
        result += "**HIGH Risk Audit Cases:** None\n\n"
    
    if filings:
        result += f"**Filing Records Found:** {len(filings)}\n\n"
        filing_types = {}
        for filing in filings:
            ftype = filing['filing_type']
            if ftype not in filing_types:
                filing_types[ftype] = []
            filing_types[ftype].append(filing)
        
        for ftype, records in filing_types.items():
            result += f"- **{ftype}:** {len(records)} records\n"
        result += "\n"
    
    result += f"💡 Type `details {pin}` to view full details."
    
    await cl.Message(content=result).send()

async def show_case_details(pin: str):
    """Show comprehensive details for a taxpayer"""
    if not pin or len(pin) != 11 or not pin.startswith('A') or not pin.endswith('P'):
        await cl.Message(content="❌ Invalid KRA PIN format. Expected: A#########P").send()
        return
    
    # Get only HIGH risk cases for this PIN
    all_cases = get_all_audit_cases()
    cases = [c for c in all_cases if c['kra_pin'] == pin and c['risk_level'] == 'HIGH']
    filings = get_filings_by_pin(pin)
    bank_txns = get_bank_transactions(pin)
    mpesa_txns = get_mpesa_transactions(pin)
    vehicles = get_vehicle_assets(pin)
    properties = get_property_assets(pin)
    imports = get_import_records(pin)
    telco = get_telco_usage(pin)
    
    if not any([cases, filings, bank_txns, mpesa_txns, vehicles, properties, imports, telco]):
        await cl.Message(content=f"📭 No data found for PIN: {pin}").send()
        return
    
    # Build comprehensive report
    report = f"""# 📋 Complete Profile: {pin}

"""
    
    # Audit Cases (only HIGH risk)
    if cases:
        report += "## 🚨 HIGH RISK Audit Cases\n\n"
        for case in cases:
            report += f"""**Case #{case['id']}** - 🔴 HIGH Risk (Score: {case['risk_score']}/100)
- Status: {case['status']}
- Declared Income: KES {case['declared_income']:,.2f}
- Inferred Income: KES {case['inferred_income']:,.2f}
- Discrepancy: KES {case['discrepancy_amount']:,.2f}
- Reason: {case['reason']}
- Created: {case['created_at']}

"""
    else:
        report += "## 🚨 Audit Cases\n\n"
        report += "No HIGH risk audit cases found for this PIN.\n\n"
    
    # Filing Records
    if filings:
        report += "## 📝 Filing Records\n\n"
        filing_types = {}
        for filing in filings:
            ftype = filing['filing_type']
            if ftype not in filing_types:
                filing_types[ftype] = {}
            section = filing['section']
            if section not in filing_types[ftype]:
                filing_types[ftype][section] = []
            filing_types[ftype][section].append(filing)
        
        for ftype, sections in filing_types.items():
            report += f"### {ftype} Filings\n\n"
            for section, records in sections.items():
                report += f"**Section {section}:**\n"
                for record in records:
                    report += f"- {record['field_name']}: {record['field_value']}\n"
                report += "\n"
    
    # Wealth Profile
    report += "## 💰 Wealth Profile\n\n"
    
    if bank_txns:
        total_bank = sum(float(t.get('amount', 0)) for t in bank_txns)
        report += f"**Bank Transactions:** {len(bank_txns)} transactions, Total: KES {total_bank:,.2f}\n\n"
    
    if mpesa_txns:
        total_mpesa = sum(float(t.get('amount', 0)) for t in mpesa_txns)
        report += f"**M-Pesa Transactions:** {len(mpesa_txns)} transactions, Total: KES {total_mpesa:,.2f}\n\n"
    
    if vehicles:
        report += f"**Vehicles:** {len(vehicles)} registered\n"
        for v in vehicles:
            report += f"- {v.get('make', 'Unknown')} {v.get('model', '')} ({v.get('registration_number', 'N/A')})\n"
        report += "\n"
    
    if properties:
        total_prop_value = sum(float(p.get('estimated_value', 0)) for p in properties)
        report += f"**Properties:** {len(properties)} properties, Total Value: KES {total_prop_value:,.2f}\n"
        for p in properties:
            report += f"- {p.get('property_type', 'Unknown')} - LR {p.get('lr_number', 'N/A')} - KES {float(p.get('estimated_value', 0)):,.2f}\n"
        report += "\n"
    
    if imports:
        total_imports = sum(float(i.get('value', 0)) for i in imports)
        report += f"**Import Records:** {len(imports)} records, Total Value: KES {total_imports:,.2f}\n\n"
    
    if telco:
        avg_telco = sum(float(t.get('monthly_spend', 0)) for t in telco) / len(telco) if telco else 0
        report += f"**Telco Usage:** {len(telco)} months, Average Monthly Spend: KES {avg_telco:,.2f}\n\n"
    
    await cl.Message(content=report).send()

async def show_help():
    """Show help message"""
    help_text = """# 📖 Admin Dashboard Help

## Available Commands:

1. **`show cases`** or **`cases`**
   - Display **ONLY HIGH RISK** audit cases
   - These cases are automatically created after taxpayers file their returns

2. **`search PIN`**
   - Search for HIGH risk cases and filings by KRA PIN
   - Example: `search A001234567P`

3. **`details PIN`** or **`detail PIN`**
   - View complete profile including:
     - HIGH risk audit cases only
     - Filing records
     - Bank transactions
     - M-Pesa records
     - Vehicle assets
     - Property assets
     - Import records
     - Telco usage
   - Example: `details A001234567P`

4. **`help`**
   - Show this help message

## Important Notes:
- ⚠️ **Only HIGH risk cases are displayed** in this dashboard
- 🔴 Cases are created automatically **after** taxpayers file their returns
- 📊 Cases appear only when significant discrepancies are detected

## Risk Levels:
- 🔴 **HIGH** (61-100): Immediate audit required - **ONLY THESE ARE SHOWN**
- 🟡 **MEDIUM** (31-60): Review recommended - **NOT DISPLAYED**
- 🟢 **LOW** (0-30): No action needed - **NOT DISPLAYED**

## Status Types:
- 📂 **OPEN**: Case is open for investigation
- 👀 **IN_REVIEW**: Under officer review
- ✅ **RESOLVED**: Case resolved
- 🔒 **CLOSED**: Case closed
"""
    await cl.Message(content=help_text).send()

