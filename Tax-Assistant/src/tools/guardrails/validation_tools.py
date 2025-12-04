import re
from typing import Optional

def validate_kra_pin(pin: str) -> dict:
    """Validates KRA PIN format (A#########P)"""
    pattern = r'^A\d{9}P$'
    is_valid = bool(re.match(pattern, pin))
    return {
        "valid": is_valid,
        "pin": pin if is_valid else None,
        "error": None if is_valid else "Invalid KRA PIN format. Expected format: A#########P"
    }

def sanitize_financial_input(amount: str) -> dict:
    """Sanitizes and validates financial inputs"""
    try:
        cleaned = re.sub(r'[^\d.]', '', str(amount))
        value = float(cleaned)
        if value < 0:
            return {"valid": False, "value": None, "error": "Amount cannot be negative"}
        return {"valid": True, "value": value, "error": None}
    except ValueError:
        return {"valid": False, "value": None, "error": "Invalid amount format"}

def validate_date_input(date_string: str) -> dict:
    """Validates date format (YYYY-MM-DD)"""
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_string):
        return {"valid": False, "date": None, "error": "Invalid date format. Expected YYYY-MM-DD"}
    
    try:
        year, month, day = map(int, date_string.split('-'))
        if not (1900 <= year <= 2100):
            return {"valid": False, "date": None, "error": "Year must be between 1900 and 2100"}
        if not (1 <= month <= 12):
            return {"valid": False, "date": None, "error": "Month must be between 1 and 12"}
        if not (1 <= day <= 31):
            return {"valid": False, "date": None, "error": "Day must be between 1 and 31"}
        return {"valid": True, "date": date_string, "error": None}
    except ValueError:
        return {"valid": False, "date": None, "error": "Invalid date values"}

def detect_prompt_injection(text: str) -> dict:
    """Scans for malicious prompts and injection attempts"""
    dangerous_patterns = [
        r'ignore\s+(previous|all|above)\s+instructions',
        r'system\s*:',
        r'<\|im_start\|>',
        r'admin\s+mode',
        r'developer\s+override',
        r'bypass\s+guardrail'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {
                "safe": False,
                "threat_detected": True,
                "message": "Potential prompt injection detected"
            }
    
    return {"safe": True, "threat_detected": False, "message": "Input appears safe"}

def emergency_audit_sanitizer(response_text: str) -> str:
    """Removes any leaked audit information from responses"""
    audit_keywords = [
        'audit_case', 'risk_score', 'risk_level', 'discrepancy',
        'inferred_income', 'flagged', 'investigation', 'compliance_check'
    ]
    
    sanitized = response_text
    for keyword in audit_keywords:
        sanitized = re.sub(
            rf'\b{keyword}\b.*?[\n.]',
            '[REDACTED]',
            sanitized,
            flags=re.IGNORECASE
        )
    
    return sanitized

def sanitize_input_text(text: str, max_length: int = 500) -> str:
    """General input sanitization"""
    cleaned = text.strip()[:max_length]
    cleaned = re.sub(r'[<>]', '', cleaned)
    return cleaned

def enforce_data_access_policy(kra_pin: str, user_role: str, requesting_pin: str) -> dict:
    """Row-level security enforcement"""
    if user_role == 'OFFICER':
        return {"allowed": True, "reason": "Officer has access to all records"}
    elif user_role == 'TAXPAYER':
        if kra_pin == requesting_pin:
            return {"allowed": True, "reason": "Taxpayer accessing own data"}
        else:
            return {"allowed": False, "reason": "Cannot access other taxpayer's data"}
    elif user_role == 'SYSTEM':
        return {"allowed": True, "reason": "System has full access"}
    else:
        return {"allowed": False, "reason": "Unknown user role"}

def handle_tool_failure(tool_name: str, error: Exception, fallback_value: any = None) -> dict:
    """Graceful degradation strategy"""
    return {
        "success": False,
        "tool_name": tool_name,
        "error_message": str(error),
        "fallback_value": fallback_value,
        "should_continue": fallback_value is not None
    }

def safe_db_query_wrapper(query_function, *args, max_retries: int = 3, **kwargs):
    """Resilient DB operations with retries"""
    import time
    
    for attempt in range(max_retries):
        try:
            result = query_function(*args, **kwargs)
            return {"success": True, "data": result, "attempts": attempt + 1}
        except Exception as error:
            if attempt == max_retries - 1:
                return {
                    "success": False,
                    "error": str(error),
                    "attempts": attempt + 1,
                    "data": None
                }
            time.sleep(0.5 * (attempt + 1))  # Exponential backoff
    
    return {"success": False, "error": "Max retries exceeded", "data": None}

def recover_incomplete_session(session_id: str, kra_pin: str) -> dict:
    """Session state recovery"""
    from src.database.db_manager import get_session_state, get_filings_by_pin
    
    session = get_session_state(session_id)
    
    if session:
        return {
            "recovered": True,
            "session_data": session,
            "message": "Session recovered successfully"
        }
    else:
        filings = get_filings_by_pin(kra_pin)
        if filings:
            return {
                "recovered": True,
                "session_data": None,
                "filings_found": len(filings),
                "message": "Previous filings found, but no active session"
            }
        else:
            return {
                "recovered": False,
                "session_data": None,
                "message": "No previous data found"
            }
