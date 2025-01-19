from config.config import PostgreConfig
from dataclasses import dataclass
from datetime import datetime
import hashlib
import psycopg2
from typing import Optional
import uuid

@dataclass
class User:
    id: str
    name: str
    password: str
    email: str
    deleted_at: Optional[datetime]

def get_connection(cfg: PostgreConfig):
    return psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )

def get_md5(password: str) -> str:
    return hashlib.md5(password).hexdigest()

def create_user(cfg: PostgreConfig, name: str, password: str, email: str) -> User:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO users (id, name, password, email, deleted_at) VALUES (%s, %s, %s, %s, %s)"
    cur.execute(query, (str(uuid.uuid4()), name, get_md5(password), email, None))
    conn.commit()
    cur.close()
    conn.close()

def get_user(cfg: PostgreConfig, id: str) -> Optional[User]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT name, password, email, deleted_at FROM users WHERE id = %s"
    cur.execute(query, (id,))
    row = cur.fetchone()
    if row is None:
        return None
    return User(*row)
