from api.model.resource import Resource
from api.config.config import ServerConfig, S3Config
from api.util.cron import create_cron_job, update_cron_job, kill_cron_job
from api.model.s3_interactor import get_all_files
from datetime import datetime
from typing import List, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import base64


def build_query(resource: Resource, server_config: ServerConfig) -> str:
    query = f'python3 {server_config.daemon_path}'
    query += f' -r {resource.id}'
    return query


def create_daemon_cron_job_for_resource(resource: Resource, server_config: ServerConfig) -> bool:
    query = build_query(resource, server_config)
    return create_cron_job(query, resource.interval, resource.id)


def update_daemon_cron_job_for_resource(resource: Resource, server_config: ServerConfig) -> bool:
    if not resource.enabled:
        kill_cron_job(resource.id)
    query = build_query(resource, server_config)
    return update_cron_job(query, resource.interval, resource.id)


def get_last_snapshot_id(cfg: S3Config, resource_id: str) -> int:
    images = get_all_files(cfg, 'images')
    htmls = get_all_files(cfg, 'htmls')
    max_id = 0
    for image in images:
        if image['Key'].startswith(resource_id):
            max_id = max(max_id, int(image['Key'].replace('.', '_').split('_')[1]))
    for html in htmls:
        if html['Key'].startswith(resource_id):
            max_id = max(max_id, int(html['Key'].replace('.', '_').split('_')[1]))
    return max_id


def get_snapshot_times_by_resource_id(cfg: S3Config, resource_id: str) -> List[Tuple[datetime, int]]:
    images = get_all_files(cfg, 'images')
    dates = []
    for i in range(len(images)):
        if images[i]['Key'].startswith(resource_id):
            dates.append((images[i]['LastModified'], i + 1))
    return dates


def get_url_image_base_64(url: str) -> str:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)
    page_height = driver.execute_script("return document.body.scrollHeight")
    page_width = driver.execute_script("return document.body.scrollWidth")
    driver.set_window_size(page_width, page_height)
    screenshot = driver.get_screenshot_as_png()
    base64_screenshot = base64.b64encode(screenshot).decode('utf-8')
    return base64_screenshot
