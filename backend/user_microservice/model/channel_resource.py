from config.config import PostgreConfig
from dataclasses import dataclass
import psycopg2
from typing import Optional, Any, Dict, List

def get_connection(cfg: PostgreConfig):
    return psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )

@dataclass
class ChannelResource:
    channel_id: str
    resource_id: str
    enabled: bool

def create_channel_resource(cfg: PostgreConfig, channel_id: str, resource_id: str) -> ChannelResource:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO channel_resource (channel_id, resource_id, enabled) VALUES (%s, %s, %s)"
    cur.execute(query, (channel_id, resource_id, True))
    conn.commit()
    cur.close()
    conn.close()

def get_channel_resource_by_resource_id(cfg: PostgreConfig, resource_id: str) -> List[ChannelResource]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT channel_id, enabled FROM channel_resource WHERE resource_id = %s"
    cur.execute(query, (resource_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return [ChannelResource(channel_id=row[0], resource_id=resource_id, enabled=row[1]) for row in result]

def change_channel_resource_enabled(cfg: PostgreConfig, channel_id: str, resource_id: str, enabled: bool) -> None:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "UPDATE channel_resource SET enabled = %s WHERE channel_id = %s AND resource_id = %s"
    cur.execute(query, (enabled, channel_id, resource_id))
    conn.commit()
    cur.close()
    conn.close()
