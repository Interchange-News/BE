import json
import os
import time
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from werkzeug.utils import secure_filename

CRAWL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

MAX_LENGTH = 5000


def crawl_naver_article(link: str):
    try:
        response = requests.get(link, headers=CRAWL_HEADERS, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        press_tag = soup.select_one("a.media_end_head_top_logo img")
        press_name = press_tag["alt"] if press_tag else "언론사 정보 없음"

        article_tag = soup.select_one("article#dic_area")
        article_text = article_tag.get_text(
            strip=True, separator="\n") if article_tag else "본문 없음"
        if len(article_text) > MAX_LENGTH:
            article_text = article_text[:MAX_LENGTH] + "..."

        return press_name, article_text
    except Exception as e:
        print(f"❌ 기사 크롤링 실패: {link} - {e}")
        return None


def scrape_news_content(news_items):
    all_data = []
    for item in news_items:
        link = item.get("link", "")
        if not link.startswith("https://n.news.naver.com"):
            continue

        result = crawl_naver_article(link)
        if result is None:
            continue

        press_name, article_text = result
        news_info = {
            "title": item["title"],
            "article": article_text,
            "pressName": press_name,
            "originallink": item["originallink"],
            "link": link,
            "pubDate": item["pubDate"],
            "description": item["description"]
        }
        all_data.append(news_info)

        print(f"✅ {press_name}: {item['title'][:30]}...")

        time.sleep(random.uniform(0.05, 0.15))  # 유연한 sleep

    return all_data


def get_main_image(url):
    try:
        chrome_options = Options()
        chrome_options.binary_location = "/opt/chrome/chrome"
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")
        chrome_options.add_argument('window-size=1392x1150')
        chrome_options.add_argument("disable-gpu")
        service = Service(executable_path="/opt/chromedriver")
        driver = webdriver.Chrome(options=chrome_options, service=service)

        # 페이지 로드
        driver.get(url)

        # 이미지 대기 및 찾기
        try:
            wait = WebDriverWait(driver, 10)
            img_element = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "img#img1")))
            img_src = img_element.get_attribute("src")
            print(f"이미지 소스 찾음: {img_src}")
        except Exception as e:
            print(f"이미지 셀렉터 찾기 실패: {e}")
            driver.save_screenshot("/tmp/screenshot.png")
            img_src = None

        # 드라이버 종료
        driver.quit()
        return img_src
    except Exception as e:
        print(f"[크롤링 실패] URL: {url}\n오류: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def lambda_handler(event, context):
    type = event.get("type")
    if type == "news_items":
        news_items = event.get("news_items")
        result = scrape_news_content(news_items)
    elif type == "url":
        url = event.get("url")
        result = get_main_image(url)
        if not url:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing 'url' parameter"})
            }

    return {
        "statusCode": 200,
        "body": json.dumps(result, ensure_ascii=False)
    }
