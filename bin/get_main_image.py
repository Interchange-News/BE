from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os
import requests

from werkzeug.utils import secure_filename

# 저장할 폴더 설정
UPLOAD_FOLDER = "static/images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 메인 이미지 가져오는 함수
def get_main_image(url):
    chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")
    # 셀레니움 설정 (Chrome Headless 모드 사용)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(chrome_driver_path)  # chromedriver 경로 설정
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기

        soup = BeautifulSoup(driver.page_source, "html.parser")
        img_tag = soup.find("img", {"id": "img1"})

        if img_tag and "src" in img_tag.attrs:
            return img_tag["src"]
        return None
    except Exception as e:
        print(f"이미지 크롤링 실패: {url} - {e}")
        return None


def download_image(url):
    base_url = os.getenv("BASE_URL")
    image_url = get_main_image(url)
    if not image_url:
        return None
    try:
        # 이미지 요청
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            filename = secure_filename(image_url.split("/")[-1].split("?")[0])  # 파일명 안전하게 변경
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            # 이미지 저장
            with open(filepath, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            return f"{base_url}/images/{filename}"

        return "Failed to download image", 400

    except Exception as e:
        return f"Error: {e}", 500