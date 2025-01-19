import psycopg2
from config.config import PostgreConfig

def migrate(cfg: PostgreConfig) -> None:
    conn = psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )
    cur = conn.cursor()
    cur.close()
    conn.close()
