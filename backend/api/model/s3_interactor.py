import boto3
from botocore.exceptions import NoCredentialsError
from api.config.config import S3Config
from typing import Any
from io import BytesIO
from PIL import Image


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
        print(f"error while bucket creation: {e}")
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
        print("invalid credentials")
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
        print(response)
        return response['Body'].read()
    except NoCredentialsError:
        print("invalid credentials")
        return None
    except Exception:
        return None


def get_object_created_at(cfg: S3Config, bucket_name: str, object_name: str) -> Any:
    s3 = boto3.client(
        's3',
        endpoint_url=cfg.connection_string,
        aws_access_key_id=cfg.aws_access_key_id,
        aws_secret_access_key=cfg.aws_secret_access_key,
    )
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_name)
        return response['LastModified']
    except NoCredentialsError:
        print("invalid credentials")
        return None
    except Exception:
        return None


def get_image(cfg: S3Config, bucket_name: str, image_name: str) -> Image.Image:
    s3 = boto3.client(
        's3',
        endpoint_url=cfg.connection_string,
        aws_access_key_id=cfg.aws_access_key_id,
        aws_secret_access_key=cfg.aws_secret_access_key,
    )
    response = s3.get_object(Bucket=bucket_name, Key=image_name)
    image_data = response['Body'].read()
    return Image.open(BytesIO(image_data))


def get_all_files(cfg: S3Config, bucket_name: str) -> Any:
    s3 = boto3.client(
        's3',
        endpoint_url=cfg.connection_string,
        aws_access_key_id=cfg.aws_access_key_id,
        aws_secret_access_key=cfg.aws_secret_access_key,
    )
    try:
        response = s3.list_objects(Bucket=bucket_name)
        if 'Contents' not in response:
            return []
        return response['Contents']
    except NoCredentialsError:
        print("invalid credentials")
        return None
    except Exception:
        return None
