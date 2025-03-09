import boto3
from botocore.exceptions import NoCredentialsError
from config.config import parse_config

cfg = parse_config()

s3 = boto3.client(
    's3',
    endpoint_url=cfg.s3.connection_string,
    aws_access_key_id=cfg.s3.aws_access_key_id,
    aws_secret_access_key=cfg.s3.aws_secret_access_key,
)

"""
# Создание нового бакета
try:
    s3.create_bucket(Bucket='images')
    print("Bucket создан успешно")
except Exception as e:
    print(f"Ошибка при создании бакета: {e}")

try:
    s3.upload_file('/home/igormeln2003/hse/diplom/repo/backend/daemon/example_screenshot_3.png', 'images', 'file_in_s3.txt')
    print("Файл загружен успешно")
except NoCredentialsError:
    print("Ошибка: отсутствуют учетные данные")
except Exception as e:
    print(f"Ошибка при загрузке файла: {e}")
"""


response = s3.get_object(Bucket='images', Key='file_in_s3.txt')
print(response['Body'].read())