import redis
import json
from typing import Optional
from api.config.config import parse_config, RedisConfig


def __connect_to_redis(cfg: RedisConfig) -> redis.Redis:
    return redis.Redis(host=cfg.host, port=cfg.port, db=cfg.db)


def save_jwt(cfg: RedisConfig, key: str, value: bool, expire_seconds=86400) -> None:
    redis_client = __connect_to_redis(cfg)
    redis_client.set(key, str(value))
    if expire_seconds:
        redis_client.expire(key, expire_seconds)


def __get_from_redis(cfg: RedisConfig, key: str) -> Optional[bool]:
    redis_client = __connect_to_redis(cfg)
    value = redis_client.get(key)
    if value is None:
        return None
    value = bool(value)
    return bool(value)


def delete_jwt(cfg: RedisConfig, key: str) -> None:
    redis_client = __connect_to_redis(cfg)
    deleted = redis_client.delete(key)
    return deleted


def check_jwt(cfg: RedisConfig, key: str) -> bool:
    jwt_value = __get_from_redis(cfg, key)
    if jwt_value is None:
        return False
    return jwt_value
