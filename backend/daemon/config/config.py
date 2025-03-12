from dataclasses import dataclass
import yaml

@dataclass
class PostgreConfig:
    database: str
    user: str
    password: str
    host: str
    port: str

@dataclass
class S3Config:
    connection_string: str
    aws_access_key_id: str
    aws_secret_access_key: str

@dataclass
class Config:
    postgres: PostgreConfig
    s3: S3Config

def parse_config() -> Config:
    with open('//home/igormeln2003/hse/diplom/repo/backend/daemon/config.yaml', 'r') as file:
        data = yaml.safe_load(file)
    return Config(
        postgres=PostgreConfig(**data['postgres']),
        s3=S3Config(**data['s3']),
    )
