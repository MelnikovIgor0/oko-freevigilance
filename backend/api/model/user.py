from api.config.config import PostgreConfig
from dataclasses import dataclass
from datetime import datetime
import hashlib
import psycopg2
from typing import Optional
import uuid

@dataclass
class User:
    id: str
    username: str
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
    return hashlib.md5(password.encode()).hexdigest()

def create_user(cfg: PostgreConfig, name: str, password: str, email: str) -> User:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO users (id, name, password, email, deleted_at) VALUES (%s, %s, %s, %s, NULL);"
    new_uid = str(uuid.uuid4())
    password_hash = get_md5(password)
    cur.execute(query, (new_uid, name, password_hash, email))
    conn.commit()
    cur.close()
    conn.close()
    return User(
        id=new_uid,
        username=name,
        password=password_hash,
        email=email,
        deleted_at=None,
    )

def get_user_by_id(cfg: PostgreConfig, id: str) -> Optional[User]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT name, password, email, deleted_at FROM users WHERE id = %s"
    cur.execute(query, (id,))
    row = cur.fetchone()
    if row is None:
        return None
    return User(
        id=id,
        username=row[0],
        password=row[1],
        email=row[2],
        deleted_at=row[3],
    )

def get_user_by_username(cfg: PostgreConfig, name: str) -> Optional[User]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT id, password, email, deleted_at FROM users WHERE name = %s"
    cur.execute(query, (name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return None
    return User(
        id=row[0],
        username=name,
        password=row[1],
        email=row[2],
        deleted_at=row[3],
    )

def get_user_by_email(cfg: PostgreConfig, email: str) -> Optional[User]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT id, name, password, deleted_at FROM users WHERE email = %s"
    cur.execute(query, (email,))
    row = cur.fetchone()
    if row is None:
        return None
    return User(
        id=row[0],
        username=row[1],
        password=row[2],
        email=email,
        deleted_at=row[3],
    )
