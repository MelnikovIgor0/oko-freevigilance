from config.config import PostgreConfig, Config, parse_config
import os
import psycopg2

def migrate(cfg: PostgreConfig) -> None:
    conn = psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )
    with open('../../db/migrations/20250101100000_init.sql', 'r') as f:
        query = f.read()
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()


def main():
    cfg = parse_config()
    print(cfg)
    migrate(cfg.postgres)


if __name__ == '__main__':
    main()
