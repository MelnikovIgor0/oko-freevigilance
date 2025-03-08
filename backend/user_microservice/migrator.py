from config.config import PostgreConfig
import os
import psycopg2

def migrate(cfg: PostgreConfig) -> None:
    conn = psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )
    query = """
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    name VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(32) NOT NULL,
    email VARCHAR(255) NOT NULL,
    deleted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resources (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    url VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1024),
    key_words VARCHAR(255)[],
  	interval VARCHAR(255) NOT NULL,
  	make_screenshot BOOLEAN NOT NULL,
  	enabled BOOLEAN NOT NULL,
  	monitoring_polygon JSONB
);

CREATE TABLE IF NOT EXISTS snapshots (
  	id VARCHAR(36) PRIMARY KEY NOT NULL,
  	resource_id VARCHAR(36) NOT NULL REFERENCES resources(id),
  	html VARCHAR(1000000) NOT NULL,
  	parsed_test VARCHAR(1000000) NOT NULL,
  	created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS channels (
  	id VARCHAR(36) PRIMARY KEY NOT NULL,
  	params JSONB NOT NULL,
  	enabled BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS channel_resource (
  	channel_id VARCHAR(36) NOT NULL REFERENCES channels(id),
  	resource_id VARCHAR(36) NOT NULL REFERENCES resources(id)
);

CREATE TABLE IF NOT EXISTS monitoring_events (
  	id VARCHAR(36) NOT NULL PRIMARY KEY,
  	name VARCHAR(255) NOT NULL,
  	snapshot_id VARCHAR(36) NOT NULL REFERENCES snapshots(id),
  	created_at TIMESTAMP NOT NULL,
  	status MONITORING_EVENT_STATUS NOT NULL
);
"""
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()
