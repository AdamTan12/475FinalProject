-- Video Stream Platform schema (PostgreSQL)
-- Tables: subscription_plans, users, payments, locations, devices, sessions

CREATE TABLE IF NOT EXISTS subscription_plans (
    plan_id   SERIAL PRIMARY KEY,
    name      VARCHAR(255) NOT NULL,
    price     DECIMAL(10, 2) NOT NULL,
    max_streams INT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id   SERIAL PRIMARY KEY,
    name      VARCHAR(255) NOT NULL,
    email     VARCHAR(255) NOT NULL UNIQUE,
    plan_id   INT NOT NULL REFERENCES subscription_plans(plan_id),
    home_location_id INT,
    account_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS locations (
    location_id SERIAL PRIMARY KEY,
    latitude  DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    description VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users
    ADD CONSTRAINT fk_home_location
    FOREIGN KEY (home_location_id) REFERENCES locations(location_id);

CREATE TABLE IF NOT EXISTS devices (
    device_id   SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name        VARCHAR(255),
    is_trusted  BOOLEAN DEFAULT FALSE,
    last_seen_at_home TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id   SERIAL PRIMARY KEY,
    user_id      INT NOT NULL REFERENCES users(user_id),
    amount       DECIMAL(10, 2) NOT NULL,
    status       VARCHAR(50) NOT NULL DEFAULT 'Pending',
    payment_date TIMESTAMPTZ DEFAULT NOW(),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id   SERIAL PRIMARY KEY,
    user_id      INT NOT NULL REFERENCES users(user_id),
    device_id    INT NOT NULL REFERENCES devices(device_id),
    location_id  INT NOT NULL REFERENCES locations(location_id),
    start_time   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time     TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_payments_status_date ON payments(status, payment_date);
CREATE INDEX IF NOT EXISTS idx_sessions_user_end ON sessions(user_id, end_time);
CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_location ON sessions(location_id);
