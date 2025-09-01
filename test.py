# -*- coding: utf-8 -*-

import requests
import json
import time
import hashlib

def generate_request_id():
    """현재 타임스탬프를 MD5 해시로 변환하여 request_id 생성"""
    timestamp = str(time.time())
    return hashlib.md5(timestamp.encode('utf-8')).hexdigest()

class CompletionExecutor:
    def __init__(self, host, api_key, request_id):
        self._host = host
        self._api_key = api_key
        self._request_id = request_id

    def execute(self, completion_request):
        headers = {
            'Authorization': self._api_key,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'text/event-stream'
        }

        with requests.post(self._host + '/v3/chat-completions/HCX-005',
                           headers=headers, json=completion_request, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    print(line.decode("utf-8"))


if __name__ == '__main__':
    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key='Bearer <api-key>',
        request_id=generate_request_id()  # 타임스탬프 MD5 해시로 동적 생성
    )

    request_data = json.loads("""{
  "messages" : [ {
    "role" : "system",
    "content" : [ {
      "type" : "text",
      "text" : "너는 영양학을 전공한 영양박사야 사람 나이대별로 섭취 칼로리에 따른 피드백을 제일 잘해\n\n예시로 나트륨이 부족한 사람은 간장 요리, 간장 게장과 같은 필요 음식이나 식품을 추천을 잘해"
    } ]
  }, {
    "role" : "user",
    "content" : [ {
      "type" : "text",
      "text" : "전체적으로 열량이 부족해요 어떻게 해야 채울 수 있죠?\n\n"
    } ]
  }, {
    "role" : "assistant",
    "content" : [ {
      "type" : "text",
      "text" : "열량(칼로리)은 우리 몸이 활동하는 데 필요한 에너지를 제공합니다. 만약 하루에 필요한 총 열량을 충분히 섭취하지 못한다면 다음과 같은 방법으로 열량을 보충할 수 있습니다.\n\n1. **건강한 지방 추가하기**: 아보카도, 견과류 (아몬드, 호두 등), 씨앗류 (치아씨드, 아마씨 등), 올리브 오일 등을 식단에 포함시키세요.\n2. **단백질 섭취 늘리기**: 닭 가슴살, 계란, 두부, 콩류 및 유제품 등의 단백질이 풍부한 음식을 더 많이 드세요. 단백질은 근육을 유지하고 성장시키며, 포만감을 주어 과식을 방지하는데 도움을 줍니다.\n3. **복합 탄수화물 선택하기**: 현미, 고구마, 통곡물 빵 등은 단순 탄수화물보다 천천히 소화되어 지속적인 에너지 공급원이 됩니다.\n4. **스낵으로 과일 주스나 스무디 대신 건조 과일 또는 견과류 활용하기**: 이러한 식품들은 휴대가 간편하고 빠르게 에너지를 보충할 수 있어 바쁜 일상 속에서도 유용합니다.\n5. **식사를 여러 번에 나눠서 먹기**: 하루 세 끼의 큰 식사 대신"
    } ]
  } ],
  "topP" : 0.8,
  "topK" : 0,
  "maxTokens" : 256,
  "temperature" : 0.5,
  "repetitionPenalty" : 1.1,
  "stop" : [ ],
  "seed" : 0,
  "includeAiFilters" : true
}""", strict=False)

    print(request_data)
    completion_executor.execute(request_data)
