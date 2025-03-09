import boto3
from botocore.exceptions import NoCredentialsError
from config.config import S3Config, parse_config
from typing import Any

def create_bucket(cfg: S3Config, bucket_name: str) -> bool:
    s3 = boto3.client(
        's3',
        endpoint_url=cfg.connection_string,
        aws_access_key_id=cfg.aws_access_key_id,
        aws_secret_access_key=cfg.aws_secret_access_key,
    )
    try:
        s3.create_bucket(Bucket=bucket_name)
        return True
    except Exception as e:
        print(f"Ошибка при создании бакета: {e}")
        return False

def add_object(cfg: S3Config, bucket_name: str, file_name: str, object_name: str) -> bool:
    s3 = boto3.client(
        's3',
        endpoint_url=cfg.connection_string,
        aws_access_key_id=cfg.aws_access_key_id,
        aws_secret_access_key=cfg.aws_secret_access_key,
    )
    try:
        s3.upload_file(file_name, bucket_name, object_name)
        return True
    except NoCredentialsError:
        print("Ошибка: отсутствуют учетные данные")
        return False
    except Exception:
        return False

def get_object(cfg: S3Config, bucket_name: str, object_name: str) -> Any:
    s3 = boto3.client(
        's3',
        endpoint_url=cfg.connection_string,
        aws_access_key_id=cfg.aws_access_key_id,
        aws_secret_access_key=cfg.aws_secret_access_key,
    )
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_name)
        return response['Body'].read()
    except NoCredentialsError:
        print("Ошибка: отсутствуют учетные данные")
        return False
    except Exception:
        return False
