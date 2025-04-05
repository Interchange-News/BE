import os
import requests
from bs4 import BeautifulSoup
import json


def get_press_list():
    """네이버 언론사 설정 페이지에서 언론사 목록과 로고 URL 가져오기"""
    url = "https://media.naver.com/channel/settings"

    # 페이지 요청
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Unable to fetch the page. Status code: {response.status_code}")
        return []

    # HTML 파싱
    soup = BeautifulSoup(response.text, 'html.parser')

    press_data = []

    # 지정한 클래스 기반으로 언론사 정보 추출
    press_items = soup.select(".ca_item")
    # print(press_items)
    for item in press_items:
        try:
            # ca_name 클래스에서 언론사 이름 추출
            name_elem = item.select_one(".ca_name")

            if not name_elem:
                continue

            press_name = name_elem.text.strip()

            # ca_m 클래스에서 이미지 URL 추출
            img_elem = item.select_one(".ca_m")
            print(img_elem)
            if not img_elem or not img_elem.has_attr('src'):
                continue

            logo_url = img_elem['src']

            # 일부 이미지 URL은 상대 경로일 수 있으므로 절대 경로로 변환
            if logo_url.startswith('//'):
                logo_url = 'https:' + logo_url

            press_data.append({
                "name": press_name,
                "logo_url": logo_url
            })

        except Exception as e:
            print(f"Error processing item: {e}")

    return press_data


def download_logos(press_data, output_dir="press_logos"):
    """언론사 로고 이미지 다운로드"""
    # 출력 디렉토리 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 언론사 이름 목록
    press_names = []

    for press in press_data:
        press_name = press["name"]
        logo_url = press["logo_url"]
        press_names.append(press_name)

        try:
            # 파일명에 사용할 수 없는 문자 제거
            safe_name = "".join([c for c in press_name if c.isalnum() or c in ' _-']).strip()
            safe_name = safe_name.replace(' ', '_')

            # 이미지 확장자 추출 (없을 경우 .png 사용)
            file_ext = os.path.splitext(logo_url.split('?')[0])[1]
            if not file_ext:
                file_ext = '.png'

            file_path = os.path.join(output_dir, f"{safe_name}{file_ext}")

            # 이미지 다운로드
            response = requests.get(logo_url, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                print(f"Downloaded: {press_name}")
            else:
                print(f"Failed to download {press_name}: Status code {response.status_code}")
        except Exception as e:
            print(f"Error downloading logo for {press_name}: {e}")

    return press_names


def main():
    print("네이버 언론사 목록 및 로고 크롤링을 시작합니다...")

    # 언론사 목록과 로고 URL 가져오기
    press_data = get_press_list()

    if not press_data:
        print("언론사 정보를 가져오지 못했습니다.")
        return

    # 결과 저장
    with open('press_data.json', 'w', encoding='utf-8') as f:
        json.dump(press_data, f, ensure_ascii=False, indent=2)

    print(f"총 {len(press_data)}개의 언론사 정보를 수집했습니다.")

    # 로고 다운로드
    press_names = download_logos(press_data)

    # 언론사 이름 목록 저장
    with open('press_names.txt', 'w', encoding='utf-8') as f:
        for name in press_names:
            f.write(name + '\n')

    print("크롤링이 완료되었습니다.")
    print("언론사 정보는 'press_data.json'에 저장되었습니다.")
    print("언론사 목록은 'press_names.txt'에 저장되었습니다.")
    print("로고 이미지는 'press_logos' 디렉토리에 저장되었습니다.")


if __name__ == "__main__":
    main()