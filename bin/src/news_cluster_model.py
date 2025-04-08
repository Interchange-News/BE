import json
from konlpy.tag import Okt
import pandas as pd
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np
import re
from get_main_image import download_image
from datetime import datetime
import os
import glob


def news_clustering():
    # 불용어 리스트 정의 (한국어 일반적인 불용어)
    stopwords = ['이', '그', '저', '것', '수', '등', '및', '더', '를', '에', '의', '가', '을', '는', '은', '로', '으로',
                 '에서', '있다', '하다', '이다', '또', '또한', '그리고', '한', '위', '때', '나', '너', '우리', '그들',
                 '것은', '데', '거', '끼', '들', '게', '여기', '저기', '같은', '매우', '무슨', '같이', '바로', '보다',
                 '어떤', '예', '때문', '이런', '저런', '그런', '좀', '많이', '적', '큰', '작은', '이미', '중', '현재',
                 '후', '앞', '오늘', '어제', '내일', '언제', '당신', '왜', '특히', '현', '다른', '새로운', '일부', '대한',
                 '어느', '지금', '속', '통해', '통한', '다음', '계속', '일단', '함께', '역시', '으로서', '기자', '대해',
                 '그것', '이것', '저것', '뭐', '누구', '어디', '언제', '어떻게', '왜', '무엇', '얼마나', '만큼',
                 '이번', '어느', '어떠한', '그런', '이런', '저런', '그렇게', '이렇게', '저렇게',
                 '있는', '없는', '하는', '되는', '있을', '없을', '하지', '되지', '않은', '않는',
                 '통해', '위해', '대해', '때문에', '의해', '따라', '따른', '관한', '관한', '대한', '있어',
                 '모든', '일부', '많은', '다른', '어떤', '이러한', '그러한', '저러한', '각각', '서로',
                 '때', '경우', '때문', '오늘', '내일', '어제', '이후', '이전', '지금', '최근', '당시',
                 '처음', '마지막', '매우', '너무', '정말', '더욱', '계속', '항상', '자주', '대부분', '전혀',
                 '관련', '내용', '제목', '기사', '뉴스', '말', '개', '명', '건', '개월', '년', '일', '월', '시간']

    # 전처리 함수 정의
    def preprocess_text(text):
        if pd.isna(text):  # 결측값 처리
            return ''

        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)

        # 특수문자 및 숫자 제거 (한글, 영문, 공백만 남김)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)

        # 숫자 제거
        text = re.sub(r'\d+', '', text)

        # 여러 개의 공백을 하나로 치환
        text = re.sub(r'\s+', ' ', text)

        # 이메일, URL 제거
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'http\S+', '', text)

        return text.strip()

    # 데이터 로드
    chunks = []
    for chunk in pd.read_csv('../news_data_politic.csv',
                             usecols=['title', 'article', 'pressName',
                                      'originallink', 'link', 'pubDate', 'description'],
                             encoding='UTF-8',
                             chunksize=1000):
        chunks.append(chunk)

    df = pd.concat(chunks)

    # 결측값 및 중복값 처리
    print(f"전처리 전 데이터 개수: {len(df)}")
    df = df.dropna(subset=['title', 'article'])  # 본문이나 제목이 없는 데이터 제거
    df = df.drop_duplicates(subset=['article'])  # 중복 기사 제거
    print(f"결측값, 중복값 제거 후 데이터 개수: {len(df)}")

    # 전처리 적용
    print("텍스트 전처리 중...")
    df['article_preprocessed'] = df['article'].apply(preprocess_text)
    df['title_preprocessed'] = df['title'].apply(preprocess_text)

    # 전처리된 본문의 길이가 너무 짧은 데이터 제거 (의미 없는 데이터일 가능성 높음)
    min_content_length = 100  # 최소 100자 이상
    df = df[df['article_preprocessed'].str.len() > min_content_length]
    print(f"짧은 본문 제거 후 데이터 개수: {len(df)}")

    # 형태소 분석 및 명사 추출
    print("형태소 분석 중...")
    okt = Okt()
    noun_list = []

    for content in tqdm(df['article_preprocessed']):
        nouns = okt.nouns(content)
        # 불용어 제거 및 2글자 이상 단어만 선택
        filtered_nouns = [
            noun for noun in nouns if noun not in stopwords and len(noun) > 1]
        noun_list.append(filtered_nouns)

    df['nouns'] = noun_list

    # 명사가 없는 행 제거
    drop_index_list = []
    for i, row in df.iterrows():
        if len(row['nouns']) == 0:
            drop_index_list.append(i)

    df = df.drop(drop_index_list)
    df = df.reset_index(drop=True)  # 인덱스 재설정
    print(f"명사 추출 후 최종 데이터 개수: {len(df)}")

    # TF-IDF 벡터화
    print("TF-IDF 벡터화 중...")
    text = [" ".join(noun) for noun in df['nouns']]

    tfidf_vectorizer = TfidfVectorizer(min_df=5, ngram_range=(1, 5))
    tfidf_vectorizer.fit(text)
    vector = tfidf_vectorizer.transform(text).toarray()

    # DBSCAN 클러스터링
    print("클러스터링 중...")
    model = DBSCAN(eps=0.6, min_samples=7, metric="cosine")
    result = model.fit_predict(vector)
    df['result'] = result
    df['result'] = df['result'].astype(int)

    # 결과 정리 및 출력
    final_result = {}
    cluster_counts = {}

    for cluster_num in set(result):
        if cluster_num == -1:
            noise_count = len(df[df['result'] == -1])
            print(f"노이즈 포인트 (클러스터링 되지 않은 기사): {noise_count}개")
            continue

        temp_df = df[df['result'] == cluster_num]
        cluster_size = len(temp_df)
        cluster_counts[cluster_num] = cluster_size

        print(f"\n클러스터 {cluster_num} (기사 {cluster_size}개):")
        final_result[cluster_num] = temp_df

        # 각 클러스터의 주요 키워드 추출 (TF-IDF 값이 높은 단어)
        cluster_indices = temp_df.index.tolist()
        cluster_vectors = vector[cluster_indices]
        cluster_avg_vector = np.mean(cluster_vectors, axis=0)

        # 상위 10개 키워드
        top_indices = cluster_avg_vector.argsort()[-10:][::-1]
        feature_names = tfidf_vectorizer.get_feature_names_out()
        top_keywords = [feature_names[i] for i in top_indices]
        print(f"주요 키워드: {', '.join(top_keywords)}")

        # 샘플 기사 제목 (최대 5개)
        print("주요 기사 제목:")
        for title in temp_df['title'][:5]:
            print(f"- {title}")

    # 정렬된 클러스터 크기 정보 출력
    print("\n클러스터 크기 분포:")
    sorted_clusters = sorted(cluster_counts.items(),
                             key=lambda x: x[1], reverse=True)

    for cluster_num, size in sorted_clusters:
        print(f"클러스터 {cluster_num}: {size}개 기사")

    clustered_data = {}

    # 기존 이미지 삭제
    image_files = glob.glob("../static/images/*")
    for image_file in image_files:
        if os.path.isfile(image_file):  # 파일인 경우에만 삭제
            try:
                os.remove(image_file)
            except Exception as e:
                print(f"파일 삭제 중 오류 발생: {e}")

    for cluster_num, cluster_size in sorted_clusters:
        # 특정 클러스터의 데이터 필터링
        temp_df = df[df['result'] == cluster_num]

        # 각 클러스터의 주요 키워드 추출
        cluster_indices = temp_df.index.tolist()
        cluster_vectors = vector[cluster_indices]
        cluster_avg_vector = np.mean(cluster_vectors, axis=0)

        top_indices = cluster_avg_vector.argsort()[-10:][::-1]
        feature_names = tfidf_vectorizer.get_feature_names_out()
        top_keywords = [feature_names[i] for i in top_indices]

        # 클러스터에 속한 기사들 정리
        articles_list = temp_df[['title', 'pressName', 'originallink', 'link', 'pubDate', 'description']].to_dict(
            orient='records')

        main_image = None

        if articles_list:
            for article in articles_list:
                try:
                    first_article_link = article['link']
                    main_image = download_image(first_article_link)
                    if main_image:
                        break
                except Exception as e:
                    print(f"이미지 다운로드 중 오류 발생: {e}")
                    continue  # 오류가 발생해도 다음 기사로 계속 진행

        # 최종 구조
        clustered_data[cluster_num] = {
            "keywords": top_keywords,
            "articles": articles_list,
            "mainImage": main_image
        }

        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {(int(k) if isinstance(k, np.int64) else k): convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, np.int64):
                return int(obj)
            elif isinstance(obj, np.float64):
                return float(obj)
            else:
                return obj

        clustered_data_list = []
        for cluster_num, cluster_data in clustered_data.items():
            # Add the cluster number to each item
            cluster_item = cluster_data.copy()
            # cluster_item['cluster_id'] = cluster_num
            clustered_data_list.append(cluster_item)

        final_data_structure = {"updatedAt": datetime.now(
        ).isoformat(), "data": clustered_data_list}
        converted_clustered_data = convert_numpy_types(final_data_structure)
        # 변환된 데이터 저장
        # converted_clustered_data = convert_numpy_types(clustered_data)

        json_filename = "../news_clusters.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(converted_clustered_data, f,
                      ensure_ascii=False, indent=4)
        print(f"클러스터링 결과가 '{json_filename}' 파일로 저장되었습니다.")

    # 분류된 애만 저장
    # filtered_df = df[(df['result'] != -1) & (df['result'] != 0)]
    # # 결과 저장
    # print("\n결과 저장 중...")
    # csv_filename = "../final_result_preprocessed2222.csv"
    # filtered_df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    # print(f"데이터가 '{csv_filename}' 파일로 저장되었습니다.")
