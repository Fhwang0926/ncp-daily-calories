# LLM Client 테스트 가이드

이 문서는 `llm_client.py` 모듈의 유닛 테스트 및 통합 테스트 사용법을 설명합니다.

## 📋 테스트 파일 구조

```
ncp-daily-calories/
├── test_llm_client.py      # 주요 유닛 테스트
├── test_llm_integration.py # 실제 API 통합 테스트  
├── test_config.py          # 테스트 설정 및 유틸리티
├── run_tests.py            # 테스트 실행 스크립트
└── README_TESTS.md         # 이 파일
```

## 🚀 빠른 시작

### 1. 모든 유닛 테스트 실행
```bash
python run_tests.py
```

### 2. 특정 테스트 클래스만 실행
```bash
python run_tests.py TestCompletionExecutor    # CompletionExecutor 테스트만
python run_tests.py TestLLMFunctions          # LLM 함수들 테스트만
python run_tests.py TestEdgeCases             # 엣지 케이스 테스트만
```

### 3. 상세 출력 모드
```bash
python run_tests.py -v
```

### 4. 실제 API 통합 테스트 (환경변수 필요)
```bash
python test_llm_integration.py
```

## 🧪 테스트 종류

### TestCompletionExecutor
- **CompletionExecutor 클래스의 핵심 기능 테스트**
- HTTP 요청/응답 처리
- 스트리밍 응답 파싱
- 에러 핸들링
- Socket.IO 연동

```python
# 테스트 예시
def test_execute_streaming_success(self):
    """성공적인 스트리밍 응답 테스트"""
    # Mock HTTP 응답 설정 후 실제 동작 검증
```

### TestLLMFunctions  
- **고수준 LLM 함수들의 동작 테스트**
- `get_comprehensive_nutrition_analysis_streaming`
- `get_nutrition_recommendation_streaming` 
- `get_reduction_recommendation_streaming`
- 통계 기반 fallback 동작

```python
# 테스트 예시
def test_get_comprehensive_nutrition_analysis_streaming_success(self):
    """종합 영양 분석 스트리밍 성공 테스트"""
    # 환경변수 Mock 후 LLM 호출 검증
```

### TestEdgeCases
- **예외 상황 및 엣지 케이스 처리**
- 잘못된 성별 입력
- 누락된 RDI 정보
- 빈 영양소 데이터
- 디버그 로깅

### TestIntegration
- **전체 워크플로우 시뮬레이션**
- 환경변수 로딩
- 실제 데이터로 통합 테스트

## 🔧 환경 설정

### 유닛 테스트 (환경변수 불필요)
```bash
# 환경변수 없이도 실행 가능
python run_tests.py
```

### 통합 테스트 (실제 API 키 필요)
```bash
# Windows
set CLOVASTUDIO_API_HOST=https://clovastudio.stream.ntruss.com
set CLOVASTUDIO_API_KEY=your_actual_api_key
set CLOVASTUDIO_REQUEST_ID=your_request_id

# Linux/Mac
export CLOVASTUDIO_API_HOST="https://clovastudio.stream.ntruss.com"
export CLOVASTUDIO_API_KEY="your_actual_api_key"  
export CLOVASTUDIO_REQUEST_ID="your_request_id"

python test_llm_integration.py
```

## 📊 테스트 결과 해석

### 성공 시
```
🎉 모든 테스트가 성공했습니다!
총 테스트: 19
성공: 19
실패: 0
에러: 0
```

### 실패 시
```
⚠️ 일부 테스트가 실패했습니다.
❌ 실패한 테스트:
   - test_name (TestClass.test_name)

💥 에러가 발생한 테스트:
   - test_error (TestClass.test_error)
```

## 🛠️ 커스터마이징

### 새로운 테스트 추가
```python
# test_llm_client.py에 추가
def test_my_new_feature(self):
    """새로운 기능 테스트"""
    result = my_function()
    self.assertIsNotNone(result)
    self.assertIn("expected_text", result)
```

### Mock 데이터 수정
```python
# test_config.py에서 샘플 데이터 수정
SAMPLE_NUTRITION_DATA = {
    "totals": {"칼로리": 2000, "단백질": 70, ...},
    # 원하는 데이터로 수정
}
```

### 새로운 테스트 케이스
```python
# test_config.py의 TestDataGenerator 사용
test_data = TestDataGenerator.get_nutrition_data("deficient")
mock_socketio = MockSocketIO()
```

## 🔍 디버깅 팁

### 1. 개별 테스트 실행
```bash
python -m unittest test_llm_client.TestCompletionExecutor.test_execute_streaming_success -v
```

### 2. 상세 로그 확인
```python
# 테스트 코드에 추가
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. Mock 상태 확인
```python
# 테스트에서 Mock 호출 확인
print(f"Mock called: {mock_object.called}")
print(f"Call count: {mock_object.call_count}")
print(f"Call args: {mock_object.call_args}")
```

## 📈 성능 테스트

### API 응답 시간 측정
```python
import time
start_time = time.time()
result = llm_function()
duration = time.time() - start_time
print(f"API 호출 시간: {duration:.2f}초")
```

### 메모리 사용량 확인
```python
import tracemalloc
tracemalloc.start()
# 테스트 실행
current, peak = tracemalloc.get_traced_memory()
print(f"메모리 사용량: 현재 {current / 1024 / 1024:.1f}MB, 최대 {peak / 1024 / 1024:.1f}MB")
```

## 🚨 주의사항

1. **실제 API 키를 테스트에 하드코딩하지 마세요**
2. **통합 테스트는 실제 API 호출 비용이 발생할 수 있습니다**
3. **테스트용 임시 파일은 자동으로 정리됩니다**
4. **Mock 테스트와 실제 API 테스트를 구분해서 실행하세요**

## 📝 기여 가이드

### 새로운 테스트 추가 시
1. `test_llm_client.py`에 적절한 클래스에 추가
2. `test_config.py`에 필요한 Mock 데이터 추가
3. 테스트 이름은 `test_기능명_상황`으로 명명
4. Docstring에 테스트 목적 명시

### 버그 수정 시
1. 해당 버그를 재현하는 테스트 먼저 작성
2. 테스트가 실패하는 것 확인
3. 코드 수정 후 테스트 통과 확인

## 🔗 관련 파일

- `llm_client.py`: 테스트 대상 모듈
- `app.py`: LLM 클라이언트를 사용하는 메인 애플리케이션
- `requirements.txt`: 필요한 Python 패키지 목록

---

🧪 **테스트를 통해 코드 품질을 높이고 안정성을 보장하세요!**
