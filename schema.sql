-- Original API response
CREATE TABLE IF NOT EXISTS raw_weather_events (
    raw_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    source TEXT NOT NULL,
    city TEXT NOT NULL,
    requested_date TEXT NOT NULL,
    ingestion_timestamp TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Clean weather rows
CREATE TABLE IF NOT EXISTS weather_observations (
    city TEXT NOT NULL,
    source TEXT NOT NULL,
    observation_date TEXT NOT NULL,
    temperature_f REAL,
    high_temperature_f REAL,
    low_temperature_f REAL,
    humidity_percent REAL,
    wind_speed_mph REAL,
    precipitation_inches REAL,
    weather_condition TEXT,
    weather_code INTEGER,
    batch_id TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (city, source, observation_date)
);

-- Details of each pipeline run
CREATE TABLE IF NOT EXISTS pipeline_runs (
    batch_id TEXT PRIMARY KEY,
    run_type TEXT NOT NULL,
    city TEXT NOT NULL,
    requested_date TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    rows_loaded INTEGER DEFAULT 0,
    error_message TEXT
);

-- Data quality checks
CREATE TABLE IF NOT EXISTS data_quality_results (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL,
    failed_count INTEGER DEFAULT 0,
    details TEXT,
    checked_at TEXT DEFAULT CURRENT_TIMESTAMP
);