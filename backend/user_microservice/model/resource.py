from config.config import PostgreConfig
from dataclasses import dataclass
import json
import psycopg2
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
    make_screenshot: bool
    enabled: bool
    polygon: Dict[str, Any]

def create_resource(
        cfg: PostgreConfig,
        url: str,
        name: str,
        description: str,
        keywords: List[str],
        interval: str,
        make_screenshot: bool,
        polygon: Dict[str, Any]
):
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO resources (id, url, name, description, key_words, interval, make_screenshot, enabled, monitoring_polygon) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    new_uid = str(uuid.uuid4())
    cur.execute(query, (new_uid, url, name, description, keywords, interval, make_screenshot, True, json.dumps(polygon)))
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
        make_screenshot=make_screenshot,
        enabled=True,
        polygon=polygon
    )

def get_resource_by_id(cfg: PostgreConfig, resource_id: str) -> Optional[Resource]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT url, name, description, key_words, interval, make_screenshot, enabled, monitoring_polygon FROM resources WHERE id = %s"
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
        polygon=result[7]
    )

def update_resource(cfg: PostgreConfig, resource_id: str, description: str, keywords: str, interval: str, enabled: bool, polygon: Dict[str, Any]) -> None:
    print('here', resource_id, description, keywords, interval, enabled, polygon)
    conn = get_connection(cfg)
    cur = conn.cursor()
    resources_table = Table('resources')
    query = Query.update(resources_table)
    print(type(query))
    if description is not None:
        query = query.set(resources_table.description, description)
    print(type(query))
    if keywords is not None:
        query = query.set(resources_table.key_words, keywords)
    print(type(query))
    if interval is not None:
        query = query.set(resources_table.interval, interval)
    print(type(query))
    if enabled is not None:
        query = query.set(resources_table.enabled, enabled)
    print(type(query))
    if polygon is not None:
        query = query.set(resources_table.monitoring_polygon, json.dumps(polygon))
    print(type(query))
    query = query.where(resources_table.id == resource_id)
    print(type(query))
    cur.execute(query.get_sql())
    conn.commit()
    cur.close()
    conn.close()
