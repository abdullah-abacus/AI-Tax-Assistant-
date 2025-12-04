-- Filing Database
CREATE TABLE IF NOT EXISTS filings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kra_pin TEXT NOT NULL,
  filing_type TEXT NOT NULL,
  section TEXT NOT NULL,
  field_name TEXT NOT NULL,
  field_value TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  session_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_filings_kra_pin ON filings(kra_pin);
CREATE INDEX IF NOT EXISTS idx_filings_session ON filings(session_id);

CREATE TABLE IF NOT EXISTS session_state (
  session_id TEXT PRIMARY KEY,
  kra_pin TEXT NOT NULL,
  filing_type TEXT NOT NULL,
  current_section TEXT,
  last_question_asked TEXT,
  responses_json TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Truth Database (Mock External Data)
CREATE TABLE IF NOT EXISTS bank_transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kra_pin TEXT NOT NULL,
  date DATE NOT NULL,
  amount REAL NOT NULL,
  type TEXT NOT NULL,
  balance REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bank_kra_pin ON bank_transactions(kra_pin);

CREATE TABLE IF NOT EXISTS mpesa_transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kra_pin TEXT NOT NULL,
  date DATE NOT NULL,
  transaction_type TEXT NOT NULL,
  amount REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mpesa_kra_pin ON mpesa_transactions(kra_pin);

CREATE TABLE IF NOT EXISTS vehicle_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kra_pin TEXT NOT NULL,
  registration_number TEXT NOT NULL,
  make TEXT NOT NULL,
  model TEXT NOT NULL,
  estimated_value REAL NOT NULL,
  purchase_date DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vehicle_kra_pin ON vehicle_assets(kra_pin);

CREATE TABLE IF NOT EXISTS property_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kra_pin TEXT NOT NULL,
  lr_number TEXT NOT NULL,
  location TEXT NOT NULL,
  property_type TEXT NOT NULL,
  estimated_value REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_property_kra_pin ON property_assets(kra_pin);

CREATE TABLE IF NOT EXISTS import_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kra_pin TEXT NOT NULL,
  date DATE NOT NULL,
  description TEXT NOT NULL,
  value REAL NOT NULL,
  customs_entry TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_import_kra_pin ON import_records(kra_pin);

CREATE TABLE IF NOT EXISTS telco_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kra_pin TEXT NOT NULL,
  month TEXT NOT NULL,
  calls_made INTEGER NOT NULL,
  data_usage_gb REAL NOT NULL,
  monthly_bill REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telco_kra_pin ON telco_usage(kra_pin);

-- Audit Database
CREATE TABLE IF NOT EXISTS audit_cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kra_pin TEXT NOT NULL,
  risk_score INTEGER,
  risk_level TEXT,
  reason TEXT,
  declared_income REAL,
  inferred_income REAL,
  discrepancy_amount REAL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'NEW'
);

CREATE INDEX IF NOT EXISTS idx_audit_kra_pin ON audit_cases(kra_pin);
CREATE INDEX IF NOT EXISTS idx_audit_risk_level ON audit_cases(risk_level);

CREATE TABLE IF NOT EXISTS access_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  kra_pin TEXT NOT NULL,
  table_name TEXT,
  action TEXT,
  user_role TEXT,
  session_id TEXT,
  ip_address TEXT
);

CREATE INDEX IF NOT EXISTS idx_access_timestamp ON access_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_access_kra_pin ON access_logs(kra_pin);
