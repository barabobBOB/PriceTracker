CREATE TABLE IF NOT EXISTS error_log (
    id SERIAL PRIMARY KEY,
    error_message TEXT,
    failed_url TEXT,
    index INTEGER,
    success BOOLEAN,
    timestamp TIMESTAMP
)