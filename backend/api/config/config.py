from dataclasses import dataclass
import yaml
import os


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
class ServerConfig:
    host: str
    port: str
    secret_key: str
    daemon_path: str
    venv_path: str
    debug: bool


@dataclass
class Config:
    postgres: PostgreConfig
    s3: S3Config
    server: ServerConfig


def parse_config() -> Config:
    config_file = os.getenv("CONFIG_FILE", "config.yaml")
    with open(config_file, "r") as file:
        data = yaml.safe_load(file)
    return Config(
        postgres=PostgreConfig(**data["postgres"]),
        s3=S3Config(**data["s3"]),
        server=ServerConfig(**data["server"]),
    )
