from config.config import PostgreConfig
from dataclasses import dataclass
import json
import psycopg2
from pypika import Table, Query
from typing import Optional, Any
import uuid

def get_connection(cfg: PostgreConfig):
    return psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )

@dataclass
class Channel:
    id: str
    params: dict[str, Any]
    enabled: bool

def create_channel(cfg: PostgreConfig, data: dict[str, Any]) -> Channel:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO channels (id, params, enabled) VALUES (%s, %s, %s)"
    new_uid = str(uuid.uuid4())
    cur.execute(query, (new_uid, json.dumps(data), True))
    conn.commit()
    cur.close()
    conn.close()
    return Channel(
        id=new_uid,
        params=data,
        enabled=True,
    )

def get_channel_by_id(cfg: PostgreConfig, channel_id: str) -> Optional[Channel]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT params, enabled FROM channels WHERE id = %s"
    cur.execute(query, (channel_id,))
    result = cur.fetchone()
    if result is None:
        return None
    return Channel(
        id=channel_id,
        params=result[0],
        enabled=result[1],
    )

def update_channel(cfg: PostgreConfig, channel_id: str, data: Optional[dict[str, Any]], enabled: Optional[bool]):
    print(data, enabled)
    conn = get_connection(cfg)
    cur = conn.cursor()
    channels_table = Table('channels')
    query = Query
    if data is not None:
        print('branch 1')
        query = query.update('channels').set(channels_table.params, json.dumps(data))
    if enabled is not None:
        print('branch 2')
        query = query.update('channels').set(channels_table.enabled, enabled)
    query = query.where(channels_table.id == channel_id)
    print('q', query, query.get_sql())
    cur.execute(query.get_sql())
    conn.commit()
    cur.close()
    conn.close()