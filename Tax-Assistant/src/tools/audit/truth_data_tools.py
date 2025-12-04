from typing import Dict, Any
from src.database.db_manager import (
    get_bank_transactions,
    get_mpesa_transactions,
    get_vehicle_assets,
    get_property_assets,
    get_import_records,
    get_telco_usage
)

def fetch_bank_data(kra_pin: str) -> Dict[str, Any]:
    """Fetch bank transaction data for KRA PIN"""
    transactions = get_bank_transactions(kra_pin)
    
    if not transactions:
        return {"kra_pin": kra_pin, "total_inflows": 0, "transaction_count": 0, "has_data": False}
    
    total_inflows = sum(t['amount'] for t in transactions if t['type'] == 'CREDIT')
    
    return {
        "kra_pin": kra_pin,
        "total_inflows": total_inflows,
        "transaction_count": len(transactions),
        "has_data": True,
        "latest_balance": transactions[-1]['balance'] if transactions else 0
    }

def fetch_mpesa_data(kra_pin: str) -> Dict[str, Any]:
    """Fetch M-Pesa transaction data for KRA PIN"""
    transactions = get_mpesa_transactions(kra_pin)
    
    if not transactions:
        return {"kra_pin": kra_pin, "total_received": 0, "transaction_count": 0, "has_data": False}
    
    total_received = sum(t['amount'] for t in transactions if t['transaction_type'] == 'RECEIVE')
    
    return {
        "kra_pin": kra_pin,
        "total_received": total_received,
        "transaction_count": len(transactions),
        "has_data": True
    }

def fetch_vehicle_data(kra_pin: str) -> Dict[str, Any]:
    """Fetch vehicle ownership data from NTSA"""
    vehicles = get_vehicle_assets(kra_pin)
    
    if not vehicles:
        return {"kra_pin": kra_pin, "vehicle_count": 0, "total_value": 0, "has_data": False}
    
    total_value = sum(v['estimated_value'] for v in vehicles)
    
    return {
        "kra_pin": kra_pin,
        "vehicle_count": len(vehicles),
        "total_value": total_value,
        "has_data": True,
        "vehicles": [{"make": v['make'], "model": v['model'], "value": v['estimated_value']} for v in vehicles]
    }

def fetch_property_data(kra_pin: str) -> Dict[str, Any]:
    """Fetch property ownership data from Lands registry"""
    properties = get_property_assets(kra_pin)
    
    if not properties:
        return {"kra_pin": kra_pin, "property_count": 0, "total_value": 0, "has_data": False}
    
    total_value = sum(p['estimated_value'] for p in properties)
    
    return {
        "kra_pin": kra_pin,
        "property_count": len(properties),
        "total_value": total_value,
        "has_data": True,
        "properties": [{"location": p['location'], "type": p['property_type'], "value": p['estimated_value']} for p in properties]
    }

def fetch_import_data(kra_pin: str) -> Dict[str, Any]:
    """Fetch customs import records"""
    imports = get_import_records(kra_pin)
    
    if not imports:
        return {"kra_pin": kra_pin, "import_count": 0, "total_value": 0, "has_data": False}
    
    total_value = sum(i['value'] for i in imports)
    
    return {
        "kra_pin": kra_pin,
        "import_count": len(imports),
        "total_value": total_value,
        "has_data": True
    }

def fetch_telco_data(kra_pin: str) -> Dict[str, Any]:
    """Fetch telco usage patterns"""
    usage = get_telco_usage(kra_pin)
    
    if not usage:
        return {"kra_pin": kra_pin, "has_data": False}
    
    total_bills = sum(u['monthly_bill'] for u in usage)
    
    return {
        "kra_pin": kra_pin,
        "months_tracked": len(usage),
        "total_bills": total_bills,
        "has_data": True
    }

def build_wealth_profile(kra_pin: str) -> Dict[str, Any]:
    """Aggregate all truth data sources for comprehensive wealth profile"""
    bank_data = fetch_bank_data(kra_pin)
    mpesa_data = fetch_mpesa_data(kra_pin)
    vehicle_data = fetch_vehicle_data(kra_pin)
    property_data = fetch_property_data(kra_pin)
    import_data = fetch_import_data(kra_pin)
    telco_data = fetch_telco_data(kra_pin)
    
    return {
        "kra_pin": kra_pin,
        "bank": bank_data,
        "mpesa": mpesa_data,
        "vehicles": vehicle_data,
        "properties": property_data,
        "imports": import_data,
        "telco": telco_data,
        "has_any_data": any([
            bank_data['has_data'],
            mpesa_data['has_data'],
            vehicle_data['has_data'],
            property_data['has_data'],
            import_data['has_data'],
            telco_data['has_data']
        ])
    }
