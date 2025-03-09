from config.config import PostgreConfig
from dataclasses import dataclass
import psycopg2
from typing import Optional, Any, Dict, List
import uuid
from datetime import datetime


def get_connection(cfg: PostgreConfig):
    return psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )


@dataclass
class MonitoringEvent:
    id: str
    resource_id: str
    snapshot_id: str
    name: str
    created_at: datetime
    status: str


def create_monitoring_event(cfg: PostgreConfig, resource_id: str, snapshot_id: str, name: str) -> MonitoringEvent:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO monitoring_events (id, resource_id, snapshot_id, name, created_at, status) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"
    event_id = str(uuid.uuid4())
    created_at = datetime.now()
    status = "created"
    cur.execute(query, (event_id, resource_id, snapshot_id, name, created_at, status))
    conn.commit()
    cur.close()
    conn.close()
    return MonitoringEvent(
        id=event_id,
        resource_id=resource_id,
        snapshot_id=snapshot_id,
        name=name,
        created_at=created_at,
        status=status
    )


def get_monitoring_event_by_id(cfg: PostgreConfig, event_id: str) -> Optional[MonitoringEvent]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT resource_id, snapshot_id, name, created_at, status FROM monitoring_events WHERE id = %s"
    cur.execute(query, (event_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is None:
        return None
    return MonitoringEvent(
        id=event_id,
        resource_id=result[0],
        snapshot_id=result[1],
        name=result[2],
        created_at=result[3],
        status=result[4]
    )

def get_monitoring_events_by_resource_id(cfg: PostgreConfig, resource_id: str) -> List[MonitoringEvent]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT id, snapshot_id, name, created_at, status FROM monitoring_events WHERE resource_id = %s"
    cur.execute(query, (resource_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return [MonitoringEvent(
        id=row[0],
        resource_id=resource_id,
        snapshot_id=row[1],
        name=row[2],
        created_at=row[3],
        status=row[4]
    ) for row in result]


def update_monitoring_event_status(cfg: PostgreConfig, event_id: str, status: str) -> None:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "UPDATE monitoring_events SET status = %s WHERE id = %s"
    cur.execute(query, (status, event_id))
    conn.commit()
    cur.close()
    conn.close()
