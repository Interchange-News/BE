import os
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import boto3
from dotenv import load_dotenv
from botocore.config import Config
import time
load_dotenv()

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

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

SEARCH_API_URL = "https://openapi.naver.com/v1/search/news.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Naver-Client-Id": NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
}

CRAWL_HEADERS = {
    "User-Agent": HEADERS["User-Agent"]
}

SAVE_PATH = "../news_data_politic.csv"
QUERY = "정치"
MAX_LENGTH = 5000


def safe_get(value):
    return '' if value is None or pd.isna(value) else value


def get_news_list(start: int = 1, display: int = 100):
    params = {
        "query": QUERY,
        "display": display,
        "start": start,
        "sort": "date"
    }
    response = requests.get(
        SEARCH_API_URL, headers=HEADERS, params=params, timeout=10)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        print(f"❌ 뉴스 검색 API 실패 - 상태코드: {response.status_code}")
        return []


def scrape_news_content():
    all_data = []
    for start in range(1, 1001, 100):
        print(f"\n🔍 뉴스 검색 시작: {start} ~ {start+99}")
        news_items = get_news_list(start)

        start_time = time.time()
        # Lambda 호출
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',  # 동기 실행
            Payload=json.dumps(
                {"type": "news_items", "news_items": news_items})
        )
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"🕒 크롤링 시간: {elapsed_time}초")

        result = json.loads(response['Payload'].read())
        articles = json.loads(result['body'])

        for article in articles:
            title = safe_get(article['title'])
            content = safe_get(article['article'])
            pressName = safe_get(article['pressName'])
            originallink = safe_get(article.get('originallink'))
            link = safe_get(article['link'])
            pubDate = safe_get(article['pubDate'])
            description = safe_get(article['description'])

            all_data.append({
                'title': title,
                'article': content,
                'pressName': pressName,
                'originallink': originallink,
                'link': link,
                'pubDate': pubDate,
                'description': description
            })

    df = pd.DataFrame(all_data)
    df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
    print(f"\n🎉 총 {len(all_data)}건 크롤링 완료. 📁 '{SAVE_PATH}' 저장 완료!")

    return all_data
