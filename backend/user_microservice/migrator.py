from config.config import PostgreConfig, Config, S3Config, parse_config
import os
import psycopg2
import boto3
from botocore.exceptions import NoCredentialsError
from config.config import parse_config

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

def init_s3_buckets(cfg: S3Config) -> None:
    s3 = boto3.client(
        's3',
        endpoint_url=cfg.connection_string,
        aws_access_key_id=cfg.aws_access_key_id,
        aws_secret_access_key=cfg.aws_secret_access_key,
    )
    s3.create_bucket(Bucket='images')
    s3.create_bucket(Bucket='htmls')

def main():
    cfg = parse_config()
    print(cfg)
    migrate(cfg.postgres)
    init_s3_buckets(cfg.s3)

if __name__ == '__main__':
    main()
