CREATE TABLE IF NOT EXISTS warrant_master (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    market TEXT NOT NULL CHECK (market IN ('TSE', 'OTC')),
    underlying_code TEXT,
    underlying_name TEXT,
    call_put TEXT CHECK (call_put IN ('CALL', 'PUT')),
    exercise_style TEXT,
    warrant_type TEXT,
    issuer TEXT,
    strike_price REAL,
    exercise_ratio REAL NOT NULL CHECK (exercise_ratio > 0),
    listed_date TEXT,
    expiry_date TEXT,
    last_trading_date TEXT,
    cap_price REAL,
    floor_price REAL,
    reset INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_quote (
    code TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    change REAL,
    volume REAL,
    trade_value REAL,
    underlying_close REAL,
    source TEXT NOT NULL,
    PRIMARY KEY (code, date)
);

CREATE TABLE IF NOT EXISTS underlying_daily (
    code TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    PRIMARY KEY (code, date)
);

CREATE TABLE IF NOT EXISTS analysis (
    code TEXT NOT NULL,
    date TEXT NOT NULL,
    iv_close REAL,
    delta REAL,
    gamma REAL,
    vega REAL,
    theta REAL,
    theoretical_price REAL,
    premium REAL,
    leverage REAL,
    moneyness REAL,
    hv20 REAL,
    breakeven REAL,
    params_snapshot TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'OK',
    PRIMARY KEY (code, date)
);

CREATE TABLE IF NOT EXISTS collect_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    market TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'PARTIAL', 'FAILED')),
    row_count INTEGER NOT NULL DEFAULT 0,
    message TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_master_underlying ON warrant_master (underlying_code);
CREATE INDEX IF NOT EXISTS idx_quote_date ON daily_quote (date);
