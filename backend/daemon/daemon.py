import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from typing import Dict, List, Optional, Tuple
import urllib.request
from bs4 import BeautifulSoup
from config.config import parse_config, PostgreConfig, S3Config
from html.parser import HTMLParser
import re
import pymorphy2
from PIL import Image
from s3_interactor import add_object, create_bucket, get_object, get_all_files, get_image
from io import BytesIO
import psycopg2
import uuid
from datetime import datetime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', type=str, required=True)
    parser.add_argument('-r', '--resource_id', type=str, required=True)
    parser.add_argument('--keywords', type=str)
    parser.add_argument('--area', type=str)
    return parser.parse_args()


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
    return words


def search_keywords(cfg: S3Config, html_path: str, keywords: List[str]) -> List[str]:
    raw_html_text = extract_text_from_html(cfg, html_path)
    words = extract_words(raw_html_text)
    found = dict()
    # вначале надо устанавливать пакет для русских слов: pip install -U pymorphy2-dicts-ru
    morph = pymorphy2.MorphAnalyzer(lang='ru')
    keywords_root = [morph.parse(keyword)[0].normal_form for keyword in keywords]
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
            result[keyword] = current_keywords[keyword] - prev_keywords[keyword]
        return result
    return current_keywords


def get_keywords_events(cfg: S3Config, html_path: str, prev_html_path: Optional[str], keywords: List[str]) -> List[str]:
    events = []
    diff = get_changed_keywords(cfg, html_path, prev_html_path, keywords)
    for word, amount in diff.items():
        if amount > 0:
            events.append(word)
    return events


def pixels_are_different(pixels1: Tuple[int, int, int], pixels2: Tuple[int, int, int]) -> bool:
    for i in range(3):
        if abs(pixels1[i] - pixels2[i]) > 20:
            return True
    return False


def get_screenshot_events(cfg: S3Config, screenshot_path: str, old_screenshot_path: Optional[str], area: str) -> bool:
    if old_screenshot_path is None:
        return False
    zone = area.split(',')
    x = int(zone[0])
    y = int(zone[1])
    width = int(zone[2])
    height = int(zone[3])
    sensitivity = int(zone[4])
    total_size = width * height
    changed_count = 0
    img1 = get_image(cfg, 'images', screenshot_path)
    img2 = get_image(cfg, 'images', old_screenshot_path)
    pixels1 = img1.load()
    pixels2 = img2.load()    
    for i in range(x, x + width):
        for j in range(y, y + height):
            if pixels_are_different(pixels1[i, j], pixels2[i, j]):
                changed_count += 1
    return changed_count * sensitivity / 100 >= total_size


def get_connection(cfg: PostgreConfig):
    return psycopg2.connect(
        database=cfg.database,
        user=cfg.user, 
        password=cfg.password,
        host=cfg.host,
        port=cfg.port,
    )


def save_monitoring_events(cfg: PostgreConfig, resource_id: str, snapshot_id: str, events: List[str], image_changed: bool) -> None:
    conn = get_connection(cfg)
    cur = conn.cursor()
    query = "INSERT INTO monitoring_events (id, name, snapshot_id, resource_id, created_at, status) VALUES (%s, %s, %s, %s, %s, %s)"
    for word in events:
        cur.execute(query, (
            str(uuid.uuid4()),
            f"keyword {word} detected",
            snapshot_id,
            resource_id,
            datetime.now().utcnow(),
            'CREATED',
        ))
    if image_changed:
        cur.execute(query, (
            str(uuid.uuid4()),
            "image changed",
            snapshot_id,
            resource_id,
            datetime.now().utcnow(),
            'CREATED',
        ))
    conn.commit()
    cur.close()
    conn.close()


def save_keywords_events(cfg: PostgreConfig, events: List[str]) -> None:
    for event in events:
        pass


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

    snapshot_id = get_last_snapshot_id(cfg.s3, args.resource_id)
    screenshot_path = None
    screenshot_prev_path = None
    html_path = None
    html_prev_path = None
    if args.keywords is not None and len(args.keywords) > 0:
        html_path = args.resource_id + '_' + str(snapshot_id + 1) + '.html'
        if snapshot_id > 0:
            html_prev_path = args.resource_id + '_' + str(snapshot_id) + '.html'
    if args.area is not None and len(args.area) > 0:
        screenshot_path = args.resource_id + '_' + str(snapshot_id + 1) + '.png'
        if snapshot_id > 0:
            screenshot_prev_path = args.resource_id + '_' + str(snapshot_id) + '.png'

    monitor_url(cfg.s3, args.url, screenshot_path, html_path)
    keyword_events = []
    if args.keywords:
        keyword_events = get_keywords_events(cfg.s3, html_path, html_prev_path, args.keywords.split(','))
    screenshot_changed = False
    if args.area:
        screenshot_changed = get_screenshot_events(cfg.s3, screenshot_path, screenshot_prev_path, args.area)
    print(keyword_events)
    print(screenshot_changed)
    save_monitoring_events(cfg.postgres, args.resource_id, args.resource_id + '_' + str(snapshot_id), keyword_events, screenshot_changed)


if __name__ == '__main__':
    main()
