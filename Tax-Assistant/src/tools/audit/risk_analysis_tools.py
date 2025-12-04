from typing import Dict, Any
from src.database.db_manager import create_audit_case
from src.tools.audit.truth_data_tools import build_wealth_profile

def calculate_inferred_income(wealth_profile: Dict[str, Any]) -> float:
    """Calculate inferred income from wealth indicators"""
    inferred = 0.0
    
    if wealth_profile['bank']['has_data']:
        inferred += wealth_profile['bank']['total_inflows']
    
    if wealth_profile['mpesa']['has_data']:
        inferred += wealth_profile['mpesa']['total_received']
    
    return inferred

def detect_discrepancy(declared: float, inferred: float) -> Dict[str, Any]:
    """Detect and quantify income discrepancy"""
    discrepancy = inferred - declared
    discrepancy_percentage = (discrepancy / declared * 100) if declared > 0 else 100
    
    return {
        "declared_income": declared,
        "inferred_income": inferred,
        "discrepancy_amount": discrepancy,
        "discrepancy_percentage": discrepancy_percentage,
        "has_discrepancy": discrepancy > 0
    }

def calculate_risk_score(declared: float, inferred: float, assets: Dict[str, Any]) -> int:
    """Calculate risk score (0-100) based on discrepancies and asset ownership"""
    score = 0
    
    discrepancy_percentage = ((inferred - declared) / declared * 100) if declared > 0 else 100
    
    if discrepancy_percentage > 200:
        score += 40
    elif discrepancy_percentage > 100:
        score += 30
    elif discrepancy_percentage > 50:
        score += 20
    elif discrepancy_percentage > 20:
        score += 10
    
    if assets['vehicles']['has_data']:
        vehicle_count = assets['vehicles']['vehicle_count']
        vehicle_value = assets['vehicles']['total_value']
        
        if vehicle_value > 20000000:
            score += 25
        elif vehicle_value > 10000000:
            score += 15
        elif vehicle_count >= 2:
            score += 10
    
    if assets['properties']['has_data']:
        property_count = assets['properties']['property_count']
        property_value = assets['properties']['total_value']
        
        if property_value > 50000000:
            score += 25
        elif property_value > 20000000:
            score += 15
        elif property_count >= 3:
            score += 10
    
    if assets['imports']['has_data']:
        import_value = assets['imports']['total_value']
        if import_value > 5000000:
            score += 15
    
    if declared == 0 and inferred > 1000000:
        score += 20
    
    return min(score, 100)

def determine_risk_level(score: int) -> str:
    """Determine risk level based on score"""
    if score >= 61:
        return "HIGH"
    elif score >= 31:
        return "MEDIUM"
    else:
        return "LOW"

def generate_audit_reason(analysis: Dict[str, Any]) -> str:
    """Generate human-readable audit reason"""
    reasons = []
    
    declared = analysis['declared_income']
    inferred = analysis['inferred_income']
    discrepancy = analysis['discrepancy_amount']
    assets = analysis['assets']
    
    if discrepancy > 0:
        reasons.append(f"Income discrepancy of KES {discrepancy:,.0f}")
        reasons.append(f"Declared: KES {declared:,.0f}, Inferred from sources: KES {inferred:,.0f}")
    
    if assets['bank']['has_data']:
        reasons.append(f"Bank inflows: KES {assets['bank']['total_inflows']:,.0f}")
    
    if assets['mpesa']['has_data']:
        reasons.append(f"M-Pesa receipts: KES {assets['mpesa']['total_received']:,.0f}")
    
    if assets['vehicles']['has_data']:
        vehicle_count = assets['vehicles']['vehicle_count']
        vehicle_value = assets['vehicles']['total_value']
        reasons.append(f"Owns {vehicle_count} vehicle(s) valued at KES {vehicle_value:,.0f}")
    
    if assets['properties']['has_data']:
        property_count = assets['properties']['property_count']
        property_value = assets['properties']['total_value']
        reasons.append(f"Owns {property_count} propert(ies) valued at KES {property_value:,.0f}")
    
    if assets['imports']['has_data']:
        import_value = assets['imports']['total_value']
        reasons.append(f"Import records totaling KES {import_value:,.0f}")
    
    return " | ".join(reasons)

def create_audit_case_if_risky(kra_pin: str, analysis: Dict[str, Any]) -> bool:
    """Create audit case ONLY if HIGH risk (after tax filing)"""
    risk_level = analysis['risk_level']
    
    # Only create cases for HIGH risk - these appear in admin dashboard
    if risk_level == 'HIGH':
        create_audit_case(
            kra_pin=kra_pin,
            risk_score=analysis['risk_score'],
            risk_level=risk_level,
            reason=analysis['reason'],
            declared_income=analysis['declared_income'],
            inferred_income=analysis['inferred_income']
        )
        return True
    
    return False

def run_full_risk_analysis(kra_pin: str, declared_income: float) -> Dict[str, Any]:
    """Run complete risk analysis pipeline"""
    wealth_profile = build_wealth_profile(kra_pin)
    
    if not wealth_profile['has_any_data']:
        return {
            "kra_pin": kra_pin,
            "risk_level": "LOW",
            "risk_score": 0,
            "reason": "No external data available for verification",
            "audit_case_created": False
        }
    
    inferred_income = calculate_inferred_income(wealth_profile)
    discrepancy_analysis = detect_discrepancy(declared_income, inferred_income)
    risk_score = calculate_risk_score(declared_income, inferred_income, wealth_profile)
    risk_level = determine_risk_level(risk_score)
    
    analysis = {
        "kra_pin": kra_pin,
        "declared_income": declared_income,
        "inferred_income": inferred_income,
        "discrepancy_amount": discrepancy_analysis['discrepancy_amount'],
        "risk_score": risk_score,
        "risk_level": risk_level,
        "assets": wealth_profile,
        "reason": generate_audit_reason({
            "declared_income": declared_income,
            "inferred_income": inferred_income,
            "discrepancy_amount": discrepancy_analysis['discrepancy_amount'],
            "assets": wealth_profile
        })
    }
    
    audit_case_created = create_audit_case_if_risky(kra_pin, analysis)
    analysis['audit_case_created'] = audit_case_created
    
    return analysis
