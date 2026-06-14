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
    high_temperature_f REAL,
    low_temperature_f REAL,
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

CREATE VIEW IF NOT EXISTS daily_weather_summary AS
SELECT
    city,
    observation_date,
    high_temperature_f,
    low_temperature_f,
    ROUND((high_temperature_f + low_temperature_f) / 2, 1) AS avg_temperature_f,
    precipitation_inches,
    weather_condition,
    weather_code
FROM weather_observations
ORDER BY city, observation_date;


CREATE VIEW IF NOT EXISTS monthly_weather_summary AS
SELECT
    city,
    STRFTIME('%Y-%m', observation_date) AS year_month,
    ROUND(AVG((high_temperature_f + low_temperature_f) / 2), 1) AS avg_temperature_f,
    ROUND(MAX(high_temperature_f), 1) AS max_temperature_f,
    ROUND(MIN(low_temperature_f), 1) AS min_temperature_f,
    ROUND(SUM(precipitation_inches), 3) AS total_precipitation_inches,
    COUNT(*) AS observation_count
FROM weather_observations
GROUP BY city, STRFTIME('%Y-%m', observation_date)
ORDER BY city, year_month;


CREATE VIEW IF NOT EXISTS city_weather_dimension AS
SELECT
    city,
    COUNT(*) AS total_observations,
    MIN(observation_date) AS first_observation_date,
    MAX(observation_date) AS last_observation_date,
    ROUND(AVG((high_temperature_f + low_temperature_f) / 2), 1) AS overall_avg_temperature_f,
    ROUND(MAX(high_temperature_f), 1) AS record_high_f,
    ROUND(MIN(low_temperature_f), 1) AS record_low_f,
    ROUND(SUM(precipitation_inches), 3) AS total_precipitation_inches
FROM weather_observations
GROUP BY city;