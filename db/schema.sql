-- Video Stream Platform schema (PostgreSQL)
-- Tables: subscription_plans, users, payments, locations, devices, sessions

CREATE TABLE IF NOT EXISTS subscription_plans (
    plan_id     SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    price       DECIMAL(10, 2) NOT NULL,
    max_streams INT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id           SERIAL PRIMARY KEY,
    name              VARCHAR(255) NOT NULL UNIQUE,
    email             VARCHAR(255) NOT NULL UNIQUE,
    plan_id           INT NOT NULL REFERENCES subscription_plans(plan_id),
    home_location_id  INT,
    account_status    VARCHAR(50) DEFAULT 'active',
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);;

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
    device_id         SERIAL PRIMARY KEY,
    user_id           INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name              VARCHAR(255),
    device_fingerprint VARCHAR(255),
    is_trusted        BOOLEAN DEFAULT FALSE,
    last_seen_at_home TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
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
    ip_address   VARCHAR(45),
    start_time   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time     TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Login/logout audit
CREATE TABLE IF NOT EXISTS login_logs (
    log_id    SERIAL PRIMARY KEY,
    user_id   INT NOT NULL REFERENCES users(user_id),
    action    VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_payments_status_date ON payments(status, payment_date);
CREATE INDEX IF NOT EXISTS idx_sessions_user_end ON sessions(user_id, end_time);
CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_location ON sessions(location_id);
CREATE INDEX IF NOT EXISTS idx_devices_user_fingerprint ON devices(user_id, device_fingerprint);

-- Migrations: add new columns to existing tables (no-op if already present)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'devices' AND column_name = 'device_fingerprint') THEN
    ALTER TABLE devices ADD COLUMN device_fingerprint VARCHAR(255);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sessions' AND column_name = 'ip_address') THEN
    ALTER TABLE sessions ADD COLUMN ip_address VARCHAR(45);
  END IF;
END $$;
