import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv
import random

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
load_dotenv()

# 네이버 뉴스 검색 API 설정
API_URL = "https://openapi.naver.com/v1/search/news.json"
HEADERS = {
    "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
    "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET")
}
# 뉴스 데이터 저장 리스트
news_data = []

def scrape_news_content():
    for start in range(1, 51, 10):
        params = {
            "query": "정치",
            "display": 10,
            "start": start,
            "sort": "date"
        }

        response = requests.get(API_URL, headers=HEADERS, params=params)

        # API 응답이 정상인지 확인
        if response.status_code == 200:
            news_list = response.json().get("items", [])

            for news in news_list:
                title = news["title"]  # 뉴스 제목
                link = news["link"]  # 뉴스 링크
                description = news['description']

                # 네이버 뉴스만 크롤링
                if link.startswith("https://n.news.naver.com"):
                    try:
                        # 네이버 뉴스 크롤링
                        news_response = requests.get(link, headers=headers, timeout=10, allow_redirects=False)
                        print(f"🔄 응답 코드: {response.status_code}")
                        if news_response.status_code == 200:
                            soup = BeautifulSoup(news_response.text, "html.parser")

                            # ✅ 언론사 이름 크롤링
                            press = soup.select_one("a.media_end_head_top_logo img")
                            press_name = press["alt"] if press else "언론사 정보 없음"

                            # ✅ 뉴스 본문 크롤링
                            article = soup.select_one("article#dic_area")
                            article_text = article.get_text(strip=True, separator="\n") if article else "본문 없음"

                            MAX_LENGTH = 5000
                            if len(article_text) > MAX_LENGTH:
                                article_text = article_text[:MAX_LENGTH] + "..."  # 1000자까지만 저장

                            # 데이터 저장
                            news_data.append({
                                "title": title,
                                "article": article_text,
                                "pressName": press_name,
                                "originallink": news['originallink'],
                                "link": news["link"],
                                "pubDate": news['pubDate'],
                                "description": description
                            })

                            print(f"✅ 크롤링 완료: {title} ({press_name})")
                        else:
                            print("크롤링 실패!!")
                    except Exception as e:
                        print(f"❌ 크롤링 실패: {link} - {e}")

                time.sleep(0.1)  # 크롤링 간격 조정 (서버 차단 방지)
        else:
            print(f"❌ API 요청 실패! 상태 코드: {response.status_code}")

    print(f"\n🎉 총 {len(news_data)}개의 뉴스 크롤링 완료!")

    csv_filename = "news_data_politic.csv"
    df = pd.DataFrame(news_data)
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")  # 한글 깨짐 방지

    print(f"📂 데이터가 '{csv_filename}' 파일로 저장됨!")

    return news_data
