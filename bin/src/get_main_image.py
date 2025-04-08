from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import os
import requests
import boto3
from werkzeug.utils import secure_filename
from botocore.config import Config
import time

# 저장할 폴더 설정
UPLOAD_FOLDER = "../static/images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

config = Config(
    connect_timeout=10,
    read_timeout=600  # 최대 10분 (600초)으로 설정
)
# Lambda 클라이언트 생성
lambda_client = boto3.client(
    'lambda', region_name='ap-southeast-2', config=config)
# CloudWatch Logs 클라이언트 생성
logs_client = boto3.client('logs', region_name='ap-southeast-2')

# 호출할 Lambda 함수 이름
function_name = 'icnews_scraping_docker'


def get_main_image(url):
    try:
        start_time = time.time()
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',  # 동기 실행
            Payload=json.dumps(
                {"type": "url", "url": url})
        )
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"🕒 크롤링 시간: {elapsed_time}초")
        result = json.loads(response['Payload'].read())
        link = json.loads(result['body'])
        return link
    except Exception as e:
        print(f"[크롤링 실패] URL: {url}\n오류: {e}")
        return None


# 이미지 다운로드 함수

def download_image(url):
    base_url = os.getenv("BASE_URL")
    image_url = get_main_image(url)

    if not image_url:
        return None

    try:
        response = requests.get(
            image_url, headers=headers, timeout=10, allow_redirects=False)
        if response.status_code == 200:
            filename = secure_filename(image_url.split("/")[-1].split("?")[0])
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            with open(filepath, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            return f"{base_url}/images/{filename}"
        else:
            print(
                f"[다운로드 실패] 상태코드: {response.status_code}, 이미지 URL: {image_url}")
            return None

    except Exception as e:
        print(f"[이미지 다운로드 오류] {image_url} - {e}")
        return None
