from api.config.config import PostgreConfig
from dataclasses import dataclass
import datetime
import json
import psycopg2
import psycopg2.extras
from pypika import Table, Query
from typing import Optional, Any, List, Dict
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
class Resource:
    id: str
    url: str
    name: str
    description: str
    keywords: List[str]
    interval: str
    starts_from: Optional[datetime.datetime]
    make_screenshot: bool
    enabled: bool
    polygon: List[Dict[str, Any]]


def create_resource(
    cfg: PostgreConfig,
    url: str,
    name: str,
    description: str,
    keywords: List[str],
    interval: str,
    starts_from: Optional[datetime.datetime],
    make_screenshot: bool,
    polygon: List[Dict[str, Any]],
):
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO resources (id, url, name, description, key_words, interval, starts_from, make_screenshot, enabled, monitoring_polygon) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    new_uid = str(uuid.uuid4())
    cur.execute(
        query,
        (
            new_uid,
            url,
            name,
            description,
            keywords,
            interval,
            starts_from,
            make_screenshot,
            True,
            json.dumps(polygon),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
    return Resource(
        id=new_uid,
        url=url,
        name=name,
        description=description,
        keywords=keywords,
        interval=interval,
        starts_from=starts_from,
        make_screenshot=make_screenshot,
        enabled=True,
        polygon=polygon,
    )


def get_resource_by_id(cfg: PostgreConfig, resource_id: str) -> Optional[Resource]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT url, name, description, key_words, interval, make_screenshot, enabled, monitoring_polygon, starts_from FROM resources WHERE id = %s"
    cur.execute(query, (resource_id,))
    result = cur.fetchone()
    if result is None:
        return None
    cur.close()
    conn.close()
    return Resource(
        id=resource_id,
        url=result[0],
        name=result[1],
        description=result[2],
        keywords=result[3],
        interval=result[4],
        make_screenshot=result[5],
        enabled=result[6],
        polygon=result[7],
        starts_from=result[8],
    )


def update_resource(
    cfg: PostgreConfig,
    resource_id: Optional[str],
    description: Optional[str],
    keywords: Optional[str],
    interval: Optional[str],
    enabled: Optional[bool],
    polygon: Optional[List[Dict[str, Any]]],
    starts_from: Optional[datetime.datetime] = None,
) -> None:
    conn = get_connection(cfg)
    cur = conn.cursor()
    resources_table = Table("resources")
    query = Query.update(resources_table)
    if description is not None:
        query = query.set(resources_table.description, description)
    if keywords is not None:
        query = query.set(resources_table.key_words, str(keywords).replace('[', '{').replace(']', '}').replace('\'', ''))
    if interval is not None:
        query = query.set(resources_table.interval, interval)
    if enabled is not None:
        query = query.set(resources_table.enabled, enabled)
    if polygon is not None:
        query = query.set(resources_table.monitoring_polygon, json.dumps(polygon))
    if starts_from is not None:
        query = query.set(resources_table.starts_from, starts_from)
    query = query.where(resources_table.id == resource_id)
    if query.get_sql() is None or len(query.get_sql()) == 0:
        return
    cur.execute(query.get_sql())
    conn.commit()
    cur.close()
    conn.close()


def get_all_resources(cfg: PostgreConfig) -> List[Resource]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT id, url, name, description, key_words, interval, make_screenshot, enabled, monitoring_polygon, starts_from FROM resources"
    cur.execute(query)
    result = cur.fetchall()
    cur.close()
    conn.close()
    print(result)
    return [
        Resource(
            id=row[0],
            url=row[1],
            name=row[2],
            description=row[3],
            keywords=row[4],
            interval=row[5],
            make_screenshot=row[6],
            enabled=row[7],
            polygon=row[8],
            starts_from=row[9],
        )
        for row in result
    ]
