from api.config.config import PostgreConfig
from dataclasses import dataclass
import psycopg2
from typing import Optional, Any, Dict, List
import uuid
from datetime import datetime
from pypika import Table, Query


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


def filter_monitoring_events(cfg: PostgreConfig,
                             resource_ids: List[str],
                             start_time: Optional[datetime],
                             end_time: Optional[datetime],
                             event_type: Optional[str],
                             offset: Optional[int],
                             limit: Optional[int]) -> List[MonitoringEvent]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    events_table = Table('monitoring_events')
    query = Query.from_(events_table).select(events_table.id,
                                             events_table.snapshot_id,
                                             events_table.resource_id,
                                             events_table.name,
                                             events_table.created_at,
                                             events_table.status)
    if resource_ids is not None:
        query = query.where(events_table.resource_id.isin(resource_ids))
    if start_time is not None:
        query = query.where(events_table.created_at >= start_time)
    if end_time is not None:
        query = query.where(events_table.created_at <= end_time)
    if event_type is not None:
        query = query.where(events_table.name.like(f'%{event_type}%'))
    query = query.orderby(events_table.created_at)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    cur.execute(query.get_sql())
    result = cur.fetchall()
    cur.close()
    conn.close()
    return [MonitoringEvent(
        id=row[0],
        snapshot_id=row[1],
        resource_id=row[2],
        name=row[3],
        created_at=row[4],
        status=row[5]
    ) for row in result]


def filter_monitoring_events_for_report(cfg: PostgreConfig,
                                        snapshot_ids: Optional[List[str]],
                                        event_ids: Optional[List[str]],
                                        offset: Optional[int],
                                        limit: Optional[int]) -> List[MonitoringEvent]:
    if (snapshot_ids is None or len(snapshot_ids) == 0) and (event_ids is None or len(event_ids) == 0):
        return []
    conn = get_connection(cfg)
    cur = conn.cursor()
    events_table = Table('monitoring_events')
    query = Query.from_(events_table).select(events_table.id,
                                             events_table.snapshot_id,
                                             events_table.resource_id,
                                             events_table.name,
                                             events_table.created_at,
                                             events_table.status)
    if snapshot_ids is not None and len(snapshot_ids) > 0 and event_ids is not None and len(event_ids) > 0:
        query = query.where(events_table.snapshot_id.isin(snapshot_ids) | events_table.id.isin(event_ids))
    elif event_ids is not None and len(event_ids) > 0:
        query = query.where(events_table.id.isin(event_ids))
    elif snapshot_ids is not None and len(snapshot_ids) > 0:
        query = query.where(events_table.snapshot_id.isin(snapshot_ids))
    query = query.orderby(events_table.created_at)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    cur.execute(query.get_sql())
    result = cur.fetchall()
    cur.close()
    conn.close()
    return [MonitoringEvent(
        id=row[0],
        snapshot_id=row[1],
        resource_id=row[2],
        name=row[3],
        created_at=row[4],
        status=row[5]
    ) for row in result]
