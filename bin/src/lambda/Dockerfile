# # ✅ ARM64를 지원하는 Amazon Linux 2 + Python 3.10 베이스 이미지
# FROM public.ecr.aws/lambda/python:3.10-arm64

# # ✅ 시스템 패키지 및 필요한 라이브러리 설치
# RUN yum -y update && \
#     yum -y install \
#     git \
#     wget \
#     curl \
#     unzip \
#     tar \
#     chromium \
#     libXcomposite \
#     libXcursor \
#     libXdamage \
#     libXext \
#     libXi \
#     libXtst \
#     cups-libs \
#     libXScrnSaver \
#     alsa-lib \
#     atk \
#     gtk3 \
#     ipa-gothic-fonts \
#     xorg-x11-fonts-100dpi \
#     xorg-x11-fonts-75dpi \
#     xorg-x11-fonts-cyrillic \
#     xorg-x11-fonts-misc \
#     xorg-x11-fonts-Type1 \
#     xorg-x11-utils && \
#     yum clean all

# # ✅ pip 패키지 설치
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # ✅ 함수 코드 복사
# COPY app/ ${LAMBDA_TASK_ROOT}

# # ✅ Lambda 핸들러 경로 지정
# CMD ["lambda_function.lambda_handler"]

# # ARM64를 지원하는 Amazon Linux 2 + Python 3.10 베이스 이미지
# FROM public.ecr.aws/lambda/python:3.10-arm64

# # 시스템 패키지 및 필요한 라이브러리 설치
# RUN yum -y update && \
#     yum -y install \
#     git \
#     wget \
#     curl \
#     unzip \
#     tar \
#     chromium \
#     libXcomposite \
#     libXcursor \
#     libXdamage \
#     libXext \
#     libXi \
#     libXtst \
#     cups-libs \
#     libXScrnSaver \
#     alsa-lib \
#     atk \
#     gtk3 \
#     ipa-gothic-fonts \
#     xorg-x11-fonts-100dpi \
#     xorg-x11-fonts-75dpi \
#     xorg-x11-fonts-cyrillic \
#     xorg-x11-fonts-misc \
#     xorg-x11-fonts-Type1 \
#     xorg-x11-utils && \
#     yum clean all

# # ChromeDriver 다운로드 및 설치 (ARM64 호환 버전)
# RUN CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
#     wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
#     unzip /tmp/chromedriver.zip -d /usr/bin/ && \
#     rm /tmp/chromedriver.zip && \
#     chmod +x /usr/bin/chromedriver

# # pip 패키지 설치 (Selenium 사용)
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # 함수 코드 복사
# COPY app/ ${LAMBDA_TASK_ROOT}

# # Lambda 핸들러 경로 지정
# CMD ["lambda_function.lambda_handler"]

FROM public.ecr.aws/lambda/python:3.9 as stage

RUN yum install -y -q sudo unzip
ENV CHROMIUM_VERSION=1002910

# Install Chromium
COPY install-browser.sh /tmp/
RUN /usr/bin/bash /tmp/install-browser.sh

FROM public.ecr.aws/lambda/python:3.9 as base

COPY chrome-deps.txt /tmp/
RUN yum install -y $(cat /tmp/chrome-deps.txt)

# Install Python dependencies for function
COPY requirements.txt /tmp/
RUN python3 -m pip install --upgrade pip -q
RUN python3 -m pip install -r /tmp/requirements.txt -q

COPY --from=stage /opt/chrome /opt/chrome
COPY --from=stage /opt/chromedriver /opt/chromedriver

# copy main.py
COPY main.py /var/task/


WORKDIR /var/task

CMD [ "main.lambda_handler" ]
