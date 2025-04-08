import boto3
import json
import time

# Lambda 클라이언트 생성
lambda_client = boto3.client('lambda', region_name='ap-southeast-2')
# CloudWatch Logs 클라이언트 생성
logs_client = boto3.client('logs', region_name='ap-southeast-2')

# 호출할 Lambda 함수 이름
function_name = 'icnews_scraping_docker'

# Lambda 호출
response = lambda_client.invoke(
    FunctionName=function_name,
    InvocationType='RequestResponse',  # 동기 실행
    Payload=json.dumps(
        {"url": "https://n.news.naver.com/mnews/article/088/0000940344"})
)

# 결과 읽기
result = json.loads(response['Payload'].read())
print("Lambda 실행 결과:", result)

# CloudWatch Logs에서 최근 로그 확인
log_group_name = f'/aws/lambda/{function_name}'
try:
    # 최근 로그 스트림 가져오기
    log_streams = logs_client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )

    if log_streams['logStreams']:
        latest_stream = log_streams['logStreams'][0]['logStreamName']

        # 로그 이벤트 가져오기
        log_events = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=latest_stream,
            limit=50  # 최근 50개의 로그 이벤트
        )

        print("\n=== Lambda 실행 로그 ===")
        for event in log_events['events']:
            print(f"{event['timestamp']}: {event['message']}")
    else:
        print("로그 스트림을 찾을 수 없습니다.")

except Exception as e:
    print(f"로그 확인 중 오류 발생: {str(e)}")
