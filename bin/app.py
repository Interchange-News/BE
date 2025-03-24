from flask import Flask, jsonify
import sqlite3
import pandas as pd
import json

app = Flask(__name__)

DB_FILE = "news_clusters.db"  # SQLite 데이터베이스 파일 이름
CSV_FILE = "final_result_preprocessed.csv"  # 저장된 클러스터링 결과 파일


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
            keywords TEXT
        )
    ''')

    # 기존 데이터 삭제 (새로운 데이터로 갱신)
    cursor.execute("DELETE FROM news_clusters")

    # CSV 데이터 로드 및 삽입
    df = pd.read_csv(CSV_FILE)

    for _, row in df.iterrows():
        cluster_id = row['result']
        title = row['제목']
        content = row['본문']
        press = row['언론사']

        # JSON 변환 시 ensure_ascii=False 추가 (한글 깨짐 방지)
        keywords = json.dumps([], ensure_ascii=False)  # 향후 키워드 분석 기능 추가 가능

        cursor.execute('''
            INSERT INTO news_clusters (cluster_id, title, content, press, keywords)
            VALUES (?, ?, ?, ?, ?)
        ''', (cluster_id, title, content, press, keywords))

    conn.commit()
    conn.close()
    print("✅ 데이터베이스 저장 완료!")


# 뉴스 클러스터링 결과 조회 API
@app.route('/news', methods=['GET'])
def get_news():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT cluster_id, title, content, press, keywords FROM news_clusters")
    rows = cursor.fetchall()

    conn.close()

    # 데이터를 JSON 형식으로 변환 (ensure_ascii=False 적용)
    news_list = []
    for row in rows:
        news_list.append({
            "cluster_id": row[0],
            "title": row[1],
            "content": row[2],
            "press": row[3],
            "keywords": json.loads(row[4])  # JSON 문자열을 리스트로 변환
        })

    # JSON 응답에서도 ensure_ascii=False 적용
    return jsonify(json.loads(json.dumps(news_list, ensure_ascii=False)))


if __name__ == '__main__':
    save_to_db()  # 실행 시 DB 저장
    app.run(debug=True)
