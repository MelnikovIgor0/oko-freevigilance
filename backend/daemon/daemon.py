import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Any
)
import urllib.request
from bs4 import BeautifulSoup
from config.config import (
    parse_config,
    NotificationConfig,
    PostgreConfig,
    S3Config
)
from dataclasses import dataclass
from html.parser import HTMLParser
import re
import pymorphy2
from PIL import Image
from s3_interactor import (
    add_object,
    create_bucket,
    get_all_files,
    get_object,
    get_image
)
from mail_iteractor import send_email
from io import BytesIO
import psycopg2
import uuid
from datetime import datetime
import telebot


@dataclass
class ResourceMonitoringParams:
    resource_id: str
    url: str
    make_screenshot: bool
    polygon: Dict[str, Any]
    keywords: List[str]
    starts_from: Optional[datetime]
    enabled: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--resource_id', type=str, required=True)
    return parser.parse_args()


def get_resource_params(cfg: PostgreConfig, resource_id: str) -> Optional[ResourceMonitoringParams]:
    conn = psycopg2.connect(
        host=cfg.host,
        database=cfg.database,
        user=cfg.user,
        password=cfg.password
    )
    cur = conn.cursor()
    cur.execute("SELECT url, monitoring_polygon, key_words, starts_from, enabled, make_screenshot FROM resources WHERE id = %s", (resource_id,))
    result = cur.fetchone()
    if result is None:
        return None
    return ResourceMonitoringParams(
        resource_id=resource_id,
        url=result[0],
        polygon=result[1],
        keywords=result[2],
        starts_from=result[3],
        enabled=result[4],
        make_screenshot=result[5]
    )


def save_screenshot(cfg: S3Config, url: str, file_name: str) -> None:
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
    driver.save_screenshot('/tmp/' + file_name)
    driver.quit()
    add_object(cfg, 'images', '/tmp/' + file_name, file_name)


def save_html(cfg: S3Config, url: str, file_name: str) -> None:
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    mystr = mybytes.decode("utf8")
    fp.close()
    with open('/tmp/' + file_name, 'w') as f:
        f.write(mystr)
    add_object(cfg, 'htmls', '/tmp/' + file_name, file_name)


def monitor_url(cfg: S3Config, url: str, screenshot_path: str, html_path: str) -> None:
    if screenshot_path:
        save_screenshot(cfg, url, screenshot_path)
    if html_path:
        save_html(cfg, url, html_path)


def extract_text_from_html(cfg: S3Config, html_path: str):
    try:
        html_content = get_object(cfg, 'htmls', html_path)
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(['script', 'style']):
            script.decompose()

        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        return str(e)


def extract_words(raw_html_text: str):
    words = re.findall(r'\b\w+\b', raw_html_text)
    return [word.lower() for word in words]


def search_keywords(cfg: S3Config, html_path: str, keywords: List[str]) -> List[str]:
    raw_html_text = extract_text_from_html(cfg, html_path)
    words = extract_words(raw_html_text)
    found = dict()
    # вначале надо устанавливать пакет для русских слов: pip install -U pymorphy2-dicts-ru
    morph = pymorphy2.MorphAnalyzer(lang='ru')
    keywords_root = [morph.parse(keyword.lower())[0].normal_form for keyword in keywords]
    words_root = [morph.parse(word)[0].normal_form for word in words]
    for keyword in keywords_root:
        amount = 0
        for word in words_root:
            if keyword == word:
                amount += 1
        found[keyword] = amount
    return found


def get_changed_keywords(cfg: S3Config, html_path: str, prev_html_path: Optional[str], keywords: List[str]) -> Dict[str, int]:
    current_keywords = search_keywords(cfg, html_path, keywords)
    if prev_html_path:
        prev_keywords = search_keywords(cfg, prev_html_path, keywords)
        result = dict()
        for keyword in keywords:
            if keyword not in prev_keywords.keys() and keyword not in current_keywords.keys():
                result[keyword] = 0
            elif keyword not in current_keywords.keys():
                result[keyword] = -prev_keywords[keyword]
            elif keyword not in prev_keywords.keys():
                result[keyword] = current_keywords[keyword]
            else:
                result[keyword] = current_keywords[keyword] - prev_keywords[keyword]
        return result
    return current_keywords


def get_keywords_events(cfg: S3Config, html_path: str, prev_html_path: Optional[str], keywords: List[str]) -> List[str]:
    events = []
    diff = get_changed_keywords(cfg, html_path, prev_html_path, keywords)
    for word, amount in diff.items():
        if amount != 0:
            events.append(word)
    return events


def pixels_are_different(pixels1: Tuple[int, int, int], pixels2: Tuple[int, int, int]) -> bool:
    for i in range(3):
        if abs(pixels1[i] - pixels2[i]) > 20:
            return True
    return False


def get_screenshot_events(cfg: S3Config, screenshot_path: str, old_screenshot_path: Optional[str], area: List[Dict[str, Any]]) -> bool:
    if old_screenshot_path is None:
        return False
    x = 0
    y = 0
    width = 10 ** 9
    height = 10 ** 9
    if isinstance(area, list) and area is not None and 'x' in area[0].keys():
        x = int(area[0]['x'])
        y = int(area[0]['y'])
        width = int(area[0]['width'])
        height = int(area[0]['height'])
        sensitivity = float(area[0]['sensitivity'])
    else:
        sensitivity = float(area['sensitivity'])
    changed_count = 0
    img1 = get_image(cfg, 'images', screenshot_path)
    img2 = get_image(cfg, 'images', old_screenshot_path)
    pixels1 = img1.load()
    pixels2 = img2.load()
    if x < 0 or y < 0:
        return False
    width = min(img1.size[0] - x, img2.size[0] - x)
    height = min(img1.size[1] - y, img2.size[1] - y)
    total_size = width * height
    for i in range(x, x + width):
        for j in range(y, y + height):
            if pixels_are_different(pixels1[i, j], pixels2[i, j]):
                changed_count += 1
    print(f"screenshot diff: {changed_count}/{total_size} pixels")
    return changed_count >= total_size * (sensitivity / 100)


def get_connection(cfg: PostgreConfig):
    return psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )


def notify_about_event_tg(token: str, chat_id: int, event_id: str, message: str) -> bool:
    try:
        bot = telebot.TeleBot(token)
        bot.send_message(chat_id, f'❗**Новое событие мониторинга: {event_id}**❗\n\n{message}', parse_mode='Markdown')
        return True
    except Exception as e:
        return False


def notify_by_all_channels(notification_config: NotificationConfig, channels_data: List[Tuple[str, str]], event_id: str, message: str) -> bool:
    notified = False
    for channel_type, channel_params in channels_data:
        if channel_type == 'telegram':
            chat_id = channel_params['chat_id']
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
            if isinstance(chat_id, int):
                notified = notify_about_event_tg(notification_config.telegram_token, chat_id, event_id, message) or notified
            elif isinstance(chat_id, list):
                for current_chat_id in chat_id:
                    current_chat = int(current_chat_id)
                    notified = notify_about_event_tg(notification_config.telegram_token, current_chat, event_id, message) or notified
        elif channel_type == 'email':
            emails = channel_params['email']
            if isinstance(emails, str):
                emails = [emails]
            notified = send_email(notification_config.email_from,
                                  notification_config.email_token,
                                  emails,
                                  message,
                                  f'обнаружено событие мониторинга: {event_id}') or notified
    return notified


def get_notification_channels(cfg: PostgreConfig, resource_id: str) -> List[Tuple[str, str]]:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "SELECT channel_id FROM channel_resource WHERE resource_id = %s AND enabled = true"
    cur.execute(query, (resource_id,))
    result = cur.fetchall()
    channel_ids = [row[0] for row in result]
    query = "SELECT type, params FROM channels WHERE id IN %s AND enabled = true"
    cur.execute(query, (tuple(channel_ids),))
    result = cur.fetchall()
    channels_data = [(row[0], row[1]) for row in result]
    cur.close()
    conn.close()
    return channels_data


def save_monitoring_events(postgre_cfg: PostgreConfig, notification_cfg: NotificationConfig, resource_id: str, snapshot_id: str, events: List[str], image_changed: bool) -> None:
    if len(events) == 0 and not image_changed:
        return
    channels_data = get_notification_channels(postgre_cfg, resource_id)
    conn = get_connection(postgre_cfg)
    cur = conn.cursor()
    query = "INSERT INTO monitoring_events (id, name, snapshot_id, resource_id, created_at, status) VALUES (%s, %s, %s, %s, %s, %s)"
    for word in events:
        status = 'CREATED'
        event_id = str(uuid.uuid4())
        event_message = f"keyword {word} detected"
        if notify_by_all_channels(notification_cfg, channels_data, event_id, event_message):
            status = 'NOTIFIED'
        cur.execute(query, (
            event_id,
            event_message,
            snapshot_id,
            resource_id,
            datetime.now().utcnow(),
            status,
        ))
    if image_changed:
        status = 'CREATED'
        event_id = str(uuid.uuid4())
        event_message = f"image changed"
        if notify_by_all_channels(notification_cfg, channels_data, event_id, event_message):
            status = 'NOTIFIED'
        cur.execute(query, (
            event_id,
            event_message,
            snapshot_id,
            resource_id,
            datetime.now().utcnow(),
            status,
        ))
    conn.commit()
    cur.close()
    conn.close()


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


def main():
    cfg = parse_config()
    print(cfg)
    args = parse_args()
    print(args)
    params = get_resource_params(cfg.postgres, args.resource_id)
    if params is None:
        print('Resource not found')
        return
    if params.starts_from is not None and params.starts_from > datetime.now().utcnow():
        print('Resource is not active')
        return
    if not params.enabled:
        print('Resource is not enabled')
        return
    print(params)

    snapshot_id = get_last_snapshot_id(cfg.s3, params.resource_id)
    screenshot_path = None
    screenshot_prev_path = None
    html_path = None
    html_prev_path = None
    if params.keywords is not None and len(params.keywords) > 0:
        html_path = params.resource_id + '_' + str(snapshot_id + 1) + '.html'
        if snapshot_id > 0:
            html_prev_path = params.resource_id + '_' + str(snapshot_id) + '.html'
    if params.make_screenshot:
        screenshot_path = params.resource_id + '_' + str(snapshot_id + 1) + '.png'
        if snapshot_id > 0:
            screenshot_prev_path = params.resource_id + '_' + str(snapshot_id) + '.png'

    monitor_url(cfg.s3, params.url, screenshot_path, html_path)
    keyword_events = []
    if params.keywords:
        keyword_events = get_keywords_events(cfg.s3, html_path, html_prev_path, params.keywords)
    screenshot_changed = False
    if params.make_screenshot:
        screenshot_changed = get_screenshot_events(cfg.s3, screenshot_path, screenshot_prev_path, params.polygon)
    print('detected keywords:')
    print(keyword_events)
    print('screenshot changed:', screenshot_changed)
    save_monitoring_events(cfg.postgres, cfg.notification, params.resource_id, params.resource_id + '_' + str(snapshot_id + 1), keyword_events, screenshot_changed)


if __name__ == '__main__':
    main()
