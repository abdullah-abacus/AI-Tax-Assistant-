import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "kra_tax.db")

@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception as error:
        connection.rollback()
        raise error
    finally:
        connection.close()

def initialize_database():
    with get_connection() as connection:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, 'r') as file:
            connection.executescript(file.read())
        
        seed_path = os.path.join(os.path.dirname(__file__), "seed_mock_data.sql")
        if os.path.exists(seed_path):
            with open(seed_path, 'r') as file:
                connection.executescript(file.read())

def safe_query(query: str, params: tuple = (), fetch_one: bool = False) -> Optional[List[Dict[str, Any]]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall() if not fetch_one else [cursor.fetchone()]
            return [{key: row[key] for key in row.keys()} for row in rows if row]
        return None

def log_access(kra_pin: str, table_name: str, action: str, user_role: str = 'SYSTEM', session_id: str = None):
    query = """
        INSERT INTO access_logs (kra_pin, table_name, action, user_role, session_id, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    safe_query(query, (kra_pin, table_name, action, user_role, session_id, 'localhost'))

def save_filing_data(kra_pin: str, filing_type: str, section: str, field_name: str, field_value: str, session_id: str):
    query = """
        INSERT INTO filings (kra_pin, filing_type, section, field_name, field_value, session_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    safe_query(query, (kra_pin, filing_type, section, field_name, field_value, session_id))
    log_access(kra_pin, 'filings', 'WRITE', 'TAXPAYER', session_id)

def get_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM session_state WHERE session_id = ?"
    results = safe_query(query, (session_id,), fetch_one=True)
    return results[0] if results else None

def update_session_state(session_id: str, kra_pin: str, filing_type: str, current_section: str, last_question: str, responses_json: str):
    existing = get_session_state(session_id)
    
    if existing:
        query = """
            UPDATE session_state 
            SET current_section = ?, last_question_asked = ?, responses_json = ?, updated_at = ?
            WHERE session_id = ?
        """
        safe_query(query, (current_section, last_question, responses_json, datetime.now().isoformat(), session_id))
    else:
        query = """
            INSERT INTO session_state (session_id, kra_pin, filing_type, current_section, last_question_asked, responses_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        safe_query(query, (session_id, kra_pin, filing_type, current_section, last_question, responses_json))

def get_bank_transactions(kra_pin: str) -> List[Dict[str, Any]]:
    query = "SELECT * FROM bank_transactions WHERE kra_pin = ? ORDER BY date"
    results = safe_query(query, (kra_pin,))
    log_access(kra_pin, 'bank_transactions', 'READ', 'SYSTEM')
    return results or []

def get_mpesa_transactions(kra_pin: str) -> List[Dict[str, Any]]:
    query = "SELECT * FROM mpesa_transactions WHERE kra_pin = ? ORDER BY date"
    results = safe_query(query, (kra_pin,))
    log_access(kra_pin, 'mpesa_transactions', 'READ', 'SYSTEM')
    return results or []

def get_vehicle_assets(kra_pin: str) -> List[Dict[str, Any]]:
    query = "SELECT * FROM vehicle_assets WHERE kra_pin = ?"
    results = safe_query(query, (kra_pin,))
    log_access(kra_pin, 'vehicle_assets', 'READ', 'SYSTEM')
    return results or []

def get_property_assets(kra_pin: str) -> List[Dict[str, Any]]:
    query = "SELECT * FROM property_assets WHERE kra_pin = ?"
    results = safe_query(query, (kra_pin,))
    log_access(kra_pin, 'property_assets', 'READ', 'SYSTEM')
    return results or []

def get_import_records(kra_pin: str) -> List[Dict[str, Any]]:
    query = "SELECT * FROM import_records WHERE kra_pin = ? ORDER BY date"
    results = safe_query(query, (kra_pin,))
    log_access(kra_pin, 'import_records', 'READ', 'SYSTEM')
    return results or []

def get_telco_usage(kra_pin: str) -> List[Dict[str, Any]]:
    query = "SELECT * FROM telco_usage WHERE kra_pin = ? ORDER BY month"
    results = safe_query(query, (kra_pin,))
    log_access(kra_pin, 'telco_usage', 'READ', 'SYSTEM')
    return results or []

def create_audit_case(kra_pin: str, risk_score: int, risk_level: str, reason: str, declared_income: float, inferred_income: float):
    discrepancy = inferred_income - declared_income
    query = """
        INSERT INTO audit_cases (kra_pin, risk_score, risk_level, reason, declared_income, inferred_income, discrepancy_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    safe_query(query, (kra_pin, risk_score, risk_level, reason, declared_income, inferred_income, discrepancy))
    log_access(kra_pin, 'audit_cases', 'WRITE', 'SYSTEM')

def get_all_audit_cases() -> List[Dict[str, Any]]:
    query = "SELECT * FROM audit_cases ORDER BY risk_score DESC, created_at DESC"
    return safe_query(query) or []

def get_filings_by_pin(kra_pin: str) -> List[Dict[str, Any]]:
    query = "SELECT * FROM filings WHERE kra_pin = ? ORDER BY created_at"
    results = safe_query(query, (kra_pin,))
    log_access(kra_pin, 'filings', 'READ', 'OFFICER')
    return results or []
