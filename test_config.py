"""
테스트 설정 및 공통 유틸리티

이 파일은 테스트에서 사용되는 공통 설정과 유틸리티 함수들을 제공합니다.
"""

import os
import tempfile
import json
from typing import Dict, Any

# 테스트용 환경변수 기본값
TEST_ENV_DEFAULTS = {
    'CLOVASTUDIO_API_HOST': 'https://clovastudio.stream.ntruss.com',
    'CLOVASTUDIO_API_KEY': 'test_api_key',
    'CLOVASTUDIO_REQUEST_ID': 'test_request_id'
}

# 테스트용 샘플 영양소 데이터
SAMPLE_NUTRITION_DATA = {
    "totals": {
        "칼로리": 1800,
        "단백질": 60,
        "탄수화물": 250,
        "지방": 50,
        "나트륨": 2000,
        "칼슘": 600,
        "철": 8,
        "비타민A": 700,
        "비타민C": 80,
        "식이섬유": 20
    },
    "male_pct": {
        "칼로리": 72.0,
        "단백질": 120.0,
        "탄수화물": 76.9,
        "지방": 90.9,
        "나트륨": 80.0,
        "칼슘": 60.0,
        "철": 80.0,
        "비타민A": 77.8,
        "비타민C": 80.0,
        "식이섬유": 80.0
    },
    "female_pct": {
        "칼로리": 90.0,
        "단백질": 150.0,
        "탄수화물": 96.2,
        "지방": 113.6,
        "나트륨": 100.0,
        "칼슘": 75.0,
        "철": 100.0,
        "비타민A": 100.0,
        "비타민C": 100.0,
        "식이섬유": 100.0
    },
    "deficient_nutrients": {
        "칼로리": 72.0,
        "나트륨": 80.0,
        "칼슘": 60.0,
        "철": 80.0,
        "비타민C": 80.0,
        "식이섬유": 80.0
    },
    "excessive_nutrients": {
        "단백질": 120.0,
        "지방": 113.6,
        "탄수화물": 96.2
    },
    "rdi_male": {
        "칼로리": 2500,
        "단백질": 50,
        "탄수화물": 325,
        "지방": 44,
        "나트륨": 2500,
        "칼슘": 1000,
        "철": 10,
        "비타민A": 900,
        "비타민C": 100,
        "식이섬유": 25
    },
    "rdi_female": {
        "칼로리": 2000,
        "단백질": 40,
        "탄수화물": 260,
        "지방": 35,
        "나트륨": 2000,
        "칼슘": 800,
        "철": 8,
        "비타민A": 700,
        "비타민C": 80,
        "식이섬유": 20
    }
}

# 테스트용 Mock LLM 응답
MOCK_LLM_RESPONSES = {
    "success": "다음은 성인 남성의 하루 영양소 섭취 분석 결과입니다:\n\n**전체 영양 상태 평가:**\n- 칼로리: 1800kcal (권장량의 72%) - 부족\n- 단백질: 60g (권장량의 120%) - 과다\n\n**우선 개선 사항:**\n1. 칼로리 섭취량 증가 필요\n2. 단백질 섭취량 조절 필요\n\n**구체적인 식단 조언:**\n- 견과류나 올리브오일 등 건강한 지방 추가\n- 단백질 양 조절하며 균형 잡힌 식사\n\n**단계별 실천 방안:**\n1. 하루 한 줌의 견과류 섭취\n2. 식사량을 점진적으로 증가\n3. 주 3회 이상 균형 잡힌 식단 구성",
    
    "empty": "",
    
    "partial": "다음은 분석 결과입니다",
    
    "error": None
}

class TestDataGenerator:
    """테스트 데이터 생성 클래스"""
    
    @staticmethod
    def get_nutrition_data(scenario: str = "normal") -> Dict[str, Any]:
        """
        시나리오별 영양소 데이터 반환
        
        Args:
            scenario: "normal", "deficient", "excessive", "empty"
        """
        if scenario == "normal":
            return SAMPLE_NUTRITION_DATA.copy()
        
        elif scenario == "deficient":
            data = SAMPLE_NUTRITION_DATA.copy()
            # 대부분 영양소를 부족하게 설정
            for nutrient in data["deficient_nutrients"]:
                data["male_pct"][nutrient] = 50.0
                data["female_pct"][nutrient] = 60.0
            data["excessive_nutrients"] = {}
            return data
        
        elif scenario == "excessive":
            data = SAMPLE_NUTRITION_DATA.copy()
            # 대부분 영양소를 과다하게 설정
            data["deficient_nutrients"] = {}
            for nutrient in ["단백질", "지방", "나트륨", "칼슘"]:
                data["excessive_nutrients"][nutrient] = 150.0
                data["male_pct"][nutrient] = 150.0
                data["female_pct"][nutrient] = 150.0
            return data
        
        elif scenario == "empty":
            data = SAMPLE_NUTRITION_DATA.copy()
            data["deficient_nutrients"] = {}
            data["excessive_nutrients"] = {}
            return data
        
        else:
            return SAMPLE_NUTRITION_DATA.copy()
    
    @staticmethod
    def get_mock_llm_response(response_type: str = "success") -> str:
        """Mock LLM 응답 반환"""
        return MOCK_LLM_RESPONSES.get(response_type, MOCK_LLM_RESPONSES["success"])

class MockSocketIO:
    """테스트용 Mock Socket.IO 클래스"""
    
    def __init__(self):
        self.emitted_events = []
    
    def emit(self, event: str, data: Any = None, room: str = None):
        """이벤트 발생 시뮬레이션"""
        self.emitted_events.append({
            'event': event,
            'data': data,
            'room': room,
            'timestamp': os.times()
        })
    
    def get_events(self, event_type: str = None) -> list:
        """발생한 이벤트 조회"""
        if event_type:
            return [e for e in self.emitted_events if e['event'] == event_type]
        return self.emitted_events
    
    def clear_events(self):
        """이벤트 기록 초기화"""
        self.emitted_events.clear()

class TestEnvironment:
    """테스트 환경 관리 클래스"""
    
    def __init__(self):
        self.original_env = {}
    
    def set_env_vars(self, env_vars: Dict[str, str]):
        """환경변수 설정 (백업 포함)"""
        for key, value in env_vars.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value
    
    def restore_env_vars(self):
        """환경변수 복원"""
        for key, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        self.original_env.clear()
    
    def clear_env_vars(self, keys: list):
        """특정 환경변수 제거"""
        for key in keys:
            self.original_env[key] = os.environ.get(key)
            os.environ.pop(key, None)

def create_temp_file(content: str, suffix: str = ".tmp") -> str:
    """임시 파일 생성"""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name

def cleanup_temp_file(filepath: str):
    """임시 파일 정리"""
    try:
        os.unlink(filepath)
    except (OSError, FileNotFoundError):
        pass

# 테스트용 assert 헬퍼 함수들
def assert_contains_keywords(text: str, keywords: list, case_sensitive: bool = False):
    """텍스트에 특정 키워드들이 포함되어 있는지 확인"""
    if not case_sensitive:
        text = text.lower()
        keywords = [k.lower() for k in keywords]
    
    missing_keywords = []
    for keyword in keywords:
        if keyword not in text:
            missing_keywords.append(keyword)
    
    if missing_keywords:
        raise AssertionError(f"Missing keywords: {missing_keywords}")

def assert_valid_nutrition_response(response: str):
    """영양 분석 응답이 유효한지 확인"""
    required_elements = ["영양", "추천", "식단"]
    assert_contains_keywords(response, required_elements)
    
    # 최소 길이 확인
    if len(response) < 50:
        raise AssertionError(f"Response too short: {len(response)} characters")

def assert_no_api_key_message(response: str):
    """API 키 관련 메시지가 없는지 확인"""
    api_key_phrases = [
        "API 키가 필요합니다",
        "API 키가 설정되지 않아",
        "LLM API가 설정되지 않아"
    ]
    
    for phrase in api_key_phrases:
        if phrase in response:
            raise AssertionError(f"Found API key message: '{phrase}' in response")

# 테스트 실행 전후 설정
def setup_test_environment():
    """테스트 환경 초기 설정"""
    # 테스트용 환경변수가 없으면 기본값 설정
    for key, default_value in TEST_ENV_DEFAULTS.items():
        if key not in os.environ:
            os.environ[key] = default_value

def teardown_test_environment():
    """테스트 환경 정리"""
    # 테스트용 환경변수 제거
    for key in TEST_ENV_DEFAULTS.keys():
        if os.environ.get(key) == TEST_ENV_DEFAULTS[key]:
            os.environ.pop(key, None)
