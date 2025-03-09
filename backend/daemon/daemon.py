import argparse
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from typing import List, Optional
import urllib.request
from bs4 import BeautifulSoup
import requests

@dataclass
class MonitoringEvent:
    found_keywords: List[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', type=str)
    parser.add_argument('--screenshot_path', type=str)
    parser.add_argument('--html_path', type=str)
    parser.add_argument('--screenshot_prev_path', type=str)
    parser.add_argument('--html_prev_path', type=str)
    parser.add_argument('--keywords', type=str, nargs='+')
    return parser.parse_args()

def save_screenshot(url: str, file_name: str) -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(2)
    page_height = driver.execute_script("return document.body.scrollHeight")
    page_width = driver.execute_script("return document.body.scrollWidth")
    driver.set_window_size(page_width, page_height)
    screenshot_path = file_name
    driver.save_screenshot(screenshot_path)
    driver.quit()

def save_html(url: str, file_name: str) -> None:
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    mystr = mybytes.decode("utf8")
    fp.close()
    with open(file_name, 'w') as f:
        f.write(mystr)

def monitor_url(args: argparse.Namespace) -> None:
    if args.screenshot_path:
        save_screenshot(args.url, args.screenshot_path)
    if args.html_path:
        save_html(args.url, args.html_path)

def extract_text_from_html(html_path: str):
    try:
        with open(html_path, 'r') as f:
            html_content = requests.get(f.read())
        html_content.raise_for_status()

        soup = BeautifulSoup(html_content, 'html.parser')

        for script in soup(['script', 'style']):
            script.decompose()

        return soup.get_text(strip=True)
    except Exception as e:
        return str(e)


def search_keywords(html_path: str, keywords: List[str]) -> List[str]:
    print(extract_text_from_html(html_path))

def main():
    args = parse_args()
    # monitor_url(args)
    search_keywords(args.html_path, args.keywords)

if __name__ == '__main__':
    main()
