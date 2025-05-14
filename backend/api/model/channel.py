from api.config.config import PostgreConfig
from dataclasses import dataclass
import json
import psycopg2
from pypika import Table, Query
from typing import Optional, Any, Dict, List
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
    type: str
    params: Dict[str, Any]
    enabled: bool
    name: str


def create_channel(
    cfg: PostgreConfig, data: dict[str, Any], type: str, name: str
) -> Channel:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO channels (id, params, enabled, name, type) VALUES (%s, %s, %s, %s, %s)"
    new_uid = str(uuid.uuid4())
    cur.execute(query, (new_uid, json.dumps(data), True, name, type))
    conn.commit()
    cur.close()
    conn.close()
    return Channel(
        id=new_uid,
        type=type,
        params=data,
        enabled=True,
        name=name,
    )


def get_channel_by_id(cfg: PostgreConfig, channel_id: str) -> Optional[Channel]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT params, enabled, name, type FROM channels WHERE id = %s"
    cur.execute(query, (channel_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is None:
        return None
    return Channel(
        id=channel_id,
        params=result[0],
        enabled=result[1],
        name=result[2],
        type=result[3],
    )


def get_channel_by_name(cfg: PostgreConfig, name: str) -> Optional[Channel]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT id, params, enabled, name, type FROM channels WHERE name = %s"
    cur.execute(query, (name,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is None:
        return None
    return Channel(
        id=result[0],
        params=result[1],
        enabled=result[2],
        name=name,
        type=result[3],
    )


def update_channel(
    cfg: PostgreConfig,
    channel_id: str,
    data: Optional[dict[str, Any]],
    enabled: Optional[bool],
):
    conn = get_connection(cfg)
    cur = conn.cursor()
    channels_table = Table("channels")
    query = Query.update("channels")
    if data is not None:
        query = query.set(channels_table.params, json.dumps(data))
    if enabled is not None:
        query = query.set(channels_table.enabled, enabled)
    query = query.where(channels_table.id == channel_id)
    if query.get_sql() is None or len(query.get_sql()) == 0:
        return
    cur.execute(query.get_sql())
    conn.commit()
    cur.close()
    conn.close()


def get_all_channels(cfg: PostgreConfig, offset: Optional[int], limit: Optional[int]) -> List[Channel]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT id, params, name, type, enabled FROM channels ORDER BY name"
    if offset is not None:
        query += " OFFSET %s" % offset
    if limit is not None:
        query += " LIMIT %s" % limit
    cur.execute(query)
    result = cur.fetchall()
    cur.close()
    conn.close()
    if result is None:
        return []
    return [
        Channel(id=row[0], params=row[1], name=row[2], type=row[3], enabled=row[4])
        for row in result
    ]
