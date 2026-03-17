CREATE TABLE IF NOT EXISTS subscription_plan (
    plan_id     SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    price       DECIMAL(10, 2) NOT NULL,
    max_streams INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS account_status (
    status_id   SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS location (
    location_id SERIAL PRIMARY KEY,
    latitude    DECIMAL(10, 7),
    longitude   DECIMAL(10, 7),
    description VARCHAR(255),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "user" (
    user_id          SERIAL PRIMARY KEY,
    name             VARCHAR(255) NOT NULL UNIQUE,
    email            VARCHAR(255) NOT NULL UNIQUE,
    plan_id          INT NOT NULL REFERENCES subscription_plan(plan_id),
    status_id        INT NOT NULL REFERENCES account_status(status_id),
    home_location_id INT REFERENCES location(location_id),
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS device (
    device_id          SERIAL PRIMARY KEY,
    user_id            INT NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    name               VARCHAR(255),
    device_type        VARCHAR(100),
    device_fingerprint VARCHAR(255) NOT NULL UNIQUE,
    is_trusted         BOOLEAN DEFAULT FALSE,
    last_seen_at_home  TIMESTAMPTZ,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session (
    session_id  SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES "user"(user_id),
    device_id   INT NOT NULL REFERENCES device(device_id),
    location_id INT NOT NULL REFERENCES location(location_id),
    start_time  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_end    ON session(user_id, end_time);
CREATE INDEX IF NOT EXISTS idx_devices_user         ON device(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_location    ON session(location_id);
