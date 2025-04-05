import os
import json
from flask import Flask, jsonify, request
import sqlite3
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from news_cluster_model import news_clustering
from news_scraping import scrape_news_content
from flask import Flask, send_from_directory
from datetime import datetime, timedelta
from flask_cors import CORS


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

DB_FILE = "../../news_clusters.db"  # SQLite 데이터베이스 파일 이름
CSV_FILE = "../../final_result_preprocessed.csv"  # 저장된 클러스터링 결과 파일
UPLOAD_FOLDER = "../static/images"
BIAS_REQUESTS_FILE = "../press_bias_requests.json"

# JSON 파일이 없으면 생성
if not os.path.exists(BIAS_REQUESTS_FILE):
    os.makedirs(os.path.dirname(BIAS_REQUESTS_FILE), exist_ok=True)
    with open(BIAS_REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)


# SQLite 데이터베이스에 클러스터링 결과 저장


def save_to_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 테이블 생성 (없으면 생성)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id INTEGER,
            title TEXT,
            content TEXT,
            press TEXT,
            keywords TEXT,
            pubDate TEXT,
            originallink TEXT,
            link TEXT
        )
    ''')

    # 기존 데이터 삭제 (새로운 데이터로 갱신)
    cursor.execute("DELETE FROM news_clusters")

    # CSV 데이터 로드 및 삽입
    df = pd.read_csv(CSV_FILE)

    for _, row in df.iterrows():
        cluster_id = row['result']
        title = row['title']
        content = row['article']
        press = row['pressName']
        pubDate = row['pubDate']
        originallink = row['originallink']
        link = row['link']

        # JSON 변환 시 ensure_ascii=False 추가 (한글 깨짐 방지)
        keywords = json.dumps([], ensure_ascii=False)  # 향후 키워드 분석 기능 추가 가능

        cursor.execute('''
            INSERT INTO news_clusters (cluster_id, title, content, press, keywords, pubDate, originallink, link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cluster_id, title, content, press, keywords, pubDate, originallink, link))

    conn.commit()
    conn.close()
    print("✅ 데이터베이스 저장 완료!")


# 뉴스 클러스터링 결과 조회 API
@app.route('/news', methods=['GET'])
def get_news():
    json_filename = "../news_clusters.json"
    with open(json_filename, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    # JSON 응답에서도 ensure_ascii=False 적용
    return jsonify(loaded_data)


@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


def scheduled_task():
    print("⏳ 12시간마다 실행되는 작업 시작...")
    scrape_news_content()
    news_clustering()
    # save_to_db()
    print("✅ 12시간마다 실행되는 작업 완료!")


# 스케줄러 실행
scheduler = BackgroundScheduler()


# 현재 시간을 기준으로 다음 12:00 설정
now = datetime.now()
next_run = now.replace(hour=12, minute=0, second=0, microsecond=0)

# 만약 현재 시간이 12시 이후라면 다음 날 12시로 설정
if now >= next_run:
    next_run += timedelta(days=1)

# 스케줄러에 작업 추가 (12시부터 시작, 이후 12시간 간격 실행)
scheduler.add_job(scheduled_task, 'interval', hours=8, next_run_time=next_run)
scheduler.start()


@app.route('/press-bias-request', methods=['POST'])
def submit_press_bias():
    try:
        data = request.json
        print(f"Received data: {data}")  # 디버깅용 로그

        # 현재 시간을 ISO 형식으로 변환
        data['created_at'] = datetime.now().isoformat()

        # 기존 데이터 읽기
        try:
            with open(BIAS_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                requests = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            requests = []

        # 새 요청 추가
        requests.append(data)

        # 파일에 저장
        with open(BIAS_REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'message': '편향성 피드백이 성공적으로 저장되었습니다.',
            'data': data
        }), 201

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"Error: {error_msg}")  # 디버깅용 로그
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}',
            'error_details': error_msg
        }), 500


if __name__ == '__main__':
    # scrape_news_content()
    # news_clustering()
    # save_to_db()  # 실행 시 DB 저장
    # scheduled_task()
    app.run(host='0.0.0.0', use_reloader=False, port=os.getenv('PORT'))
