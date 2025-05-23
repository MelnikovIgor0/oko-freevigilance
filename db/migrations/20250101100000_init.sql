
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(32) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    deleted_at TIMESTAMP,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS resources (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    url VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1024),
    key_words VARCHAR(255)[],
    interval VARCHAR(255) NOT NULL,
    starts_from TIMESTAMP,
    make_screenshot BOOLEAN NOT NULL,
    enabled BOOLEAN NOT NULL,
    monitoring_polygon JSONB
);

CREATE TABLE IF NOT EXISTS channels (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(100) NOT NULL,
    params JSONB NOT NULL,
    enabled BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS channel_resource (
    channel_id VARCHAR(36) NOT NULL REFERENCES channels(id),
    resource_id VARCHAR(36) NOT NULL REFERENCES resources(id),
    enabled BOOLEAN NOT NULL
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'monitoring_event_status') THEN
        CREATE TYPE MONITORING_EVENT_STATUS AS ENUM ('CREATED', 'NOTIFIED', 'WATCHED', 'REACTED');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS monitoring_events (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    snapshot_id VARCHAR(46) NOT NULL,
    resource_id VARCHAR(36) NOT NULL REFERENCES resources(id),
    created_at TIMESTAMP NOT NULL,
    status MONITORING_EVENT_STATUS NOT NULL
);
