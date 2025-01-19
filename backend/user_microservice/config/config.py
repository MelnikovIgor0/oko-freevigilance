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
class ServerConfig:
    port: str
    secret_key: str

@dataclass
class Config:
    postgres: PostgreConfig
    server: ServerConfig

def parse_config() -> Config:
    with open('config.yaml', 'r') as file:
        data = yaml.safe_load(file)
    return Config(
        postgres=PostgreConfig(**data['postgres']),
        server=ServerConfig(**data['server']),
    )
