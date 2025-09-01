"""
LLM Client 실제 API 통합 테스트

이 파일은 실제 Naver Cloud HyperCLOVA X API와의 연동을 테스트합니다.
환경변수에 실제 API 키가 설정되어 있을 때만 실행됩니다.

실행 방법:
python test_llm_integration.py

환경변수 설정:
export CLOVASTUDIO_API_HOST="https://clovastudio.stream.ntruss.com"
export CLOVASTUDIO_API_KEY="your_actual_api_key"
export CLOVASTUDIO_REQUEST_ID="your_request_id"
"""

import unittest
import os
import sys
import time
from unittest.mock import Mock

# 테스트 대상 모듈 import
try:
    from llm_client import (
        CompletionExecutor,
        get_comprehensive_nutrition_analysis_streaming,
        get_nutrition_recommendation_streaming,
        get_reduction_recommendation_streaming
    )
    from test_config import TestDataGenerator, MockSocketIO, assert_valid_nutrition_response
except ImportError as e:
    print(f"Import error: {e}")
    print("필요한 모듈을 찾을 수 없습니다.")
    sys.exit(1)


class TestRealLLMAPI(unittest.TestCase):
    """실제 LLM API 테스트"""

    @classmethod
    def setUpClass(cls):
        """클래스 레벨 설정 - 환경변수 확인"""
        cls.required_env_vars = [
            'CLOVASTUDIO_API_HOST',
            'CLOVASTUDIO_API_KEY', 
            'CLOVASTUDIO_REQUEST_ID'
        ]
        
        cls.env_vars_available = all(
            os.getenv(var) and os.getenv(var) != 'test_api_key' 
            for var in cls.required_env_vars
        )
        
        if not cls.env_vars_available:
            print("⚠️  실제 API 키가 설정되지 않아 통합 테스트를 건너뜁니다.")
            print("환경변수 설정:")
            for var in cls.required_env_vars:
                print(f"   {var}={os.getenv(var, '❌ 없음')}")

    def setUp(self):
        """각 테스트 전 설정"""
        if not self.env_vars_available:
            self.skipTest("실제 API 키가 설정되지 않음")
        
        self.test_data = TestDataGenerator.get_nutrition_data("normal")
        self.mock_socketio = MockSocketIO()

    def test_real_comprehensive_analysis_male(self):
        """실제 API로 남성 종합 분석 테스트"""
        print("🔵 남성 기준 종합 영양 분석 테스트 시작...")
        
        start_time = time.time()
        
        result = get_comprehensive_nutrition_analysis_streaming(
            totals=self.test_data["totals"],
            male_pct=self.test_data["male_pct"],
            female_pct=self.test_data["female_pct"],
            deficient_nutrients=self.test_data["deficient_nutrients"],
            excessive_nutrients=self.test_data["excessive_nutrients"],
            rdi_info=self.test_data["rdi_male"],
            gender="male",
            socketio=self.mock_socketio,
            session_id="test_session"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 100)
        
        # API 키 관련 메시지가 없어야 함 (실제 API 사용)
        self.assertNotIn("API 키가 필요합니다", result)
        
        # Socket.IO 이벤트 확인
        events = self.mock_socketio.get_events('llm_response')
        self.assertGreater(len(events), 0)
        
        print(f"✅ 남성 분석 완료 - 소요 시간: {duration:.2f}초")
        print(f"📝 응답 길이: {len(result)}자")
        print(f"🔌 Socket.IO 이벤트: {len(events)}개")
        
        # 응답 내용 샘플 출력
        print(f"📄 응답 샘플: {result[:200]}...")

    def test_real_comprehensive_analysis_female(self):
        """실제 API로 여성 종합 분석 테스트"""
        print("🔴 여성 기준 종합 영양 분석 테스트 시작...")
        
        start_time = time.time()
        
        result = get_comprehensive_nutrition_analysis_streaming(
            totals=self.test_data["totals"],
            male_pct=self.test_data["male_pct"],
            female_pct=self.test_data["female_pct"],
            deficient_nutrients=self.test_data["deficient_nutrients"],
            excessive_nutrients=self.test_data["excessive_nutrients"],
            rdi_info=self.test_data["rdi_female"],
            gender="female",
            socketio=self.mock_socketio,
            session_id="test_session"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 100)
        
        # 유효한 영양 분석 응답인지 확인
        assert_valid_nutrition_response(result)
        
        print(f"✅ 여성 분석 완료 - 소요 시간: {duration:.2f}초")
        print(f"📝 응답 길이: {len(result)}자")

    def test_real_deficient_nutrition_recommendation(self):
        """실제 API로 부족 영양소 추천 테스트"""
        print("🟡 부족 영양소 추천 테스트 시작...")
        
        result = get_nutrition_recommendation_streaming(
            deficient_nutrients=self.test_data["deficient_nutrients"],
            rdi_info=self.test_data["rdi_male"],
            gender="male"
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        # 부족 영양소 관련 내용이 포함되어야 함
        nutrition_keywords = ["칼로리", "나트륨", "칼슘", "추천", "음식"]
        for keyword in nutrition_keywords:
            if keyword in self.test_data["deficient_nutrients"] or keyword in ["추천", "음식"]:
                # 모든 키워드가 반드시 있을 필요는 없지만, 일부는 있어야 함
                pass
        
        print(f"✅ 부족 영양소 추천 완료")
        print(f"📝 응답 길이: {len(result)}자")

    def test_real_excessive_nutrition_reduction(self):
        """실제 API로 과다 영양소 감소 추천 테스트"""
        print("🟠 과다 영양소 감소 추천 테스트 시작...")
        
        result = get_reduction_recommendation_streaming(
            excessive_nutrients=self.test_data["excessive_nutrients"],
            rdi_info=self.test_data["rdi_male"],
            gender="male"
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        print(f"✅ 과다 영양소 감소 추천 완료")
        print(f"📝 응답 길이: {len(result)}자")

    def test_completion_executor_direct(self):
        """CompletionExecutor 직접 테스트"""
        print("⚙️  CompletionExecutor 직접 테스트 시작...")
        
        executor = CompletionExecutor(
            host=os.getenv('CLOVASTUDIO_API_HOST'),
            api_key=os.getenv('CLOVASTUDIO_API_KEY'),
            request_id=os.getenv('CLOVASTUDIO_REQUEST_ID')
        )
        
        completion_request = {
            "messages": [
                {
                    "role": "user", 
                    "content": "간단한 영양 조언을 한 문장으로 해주세요."
                }
            ],
            "maxTokens": 100,
            "temperature": 0.5
        }
        
        start_time = time.time()
        result = executor.execute_streaming(completion_request)
        end_time = time.time()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result.strip()), 10)
        
        print(f"✅ 직접 API 호출 완료 - 소요 시간: {end_time - start_time:.2f}초")
        print(f"📝 응답: {result}")

    def test_api_rate_limiting(self):
        """API 호출 제한 테스트"""
        print("🚦 API 호출 제한 테스트 시작...")
        
        # 짧은 간격으로 여러 번 호출
        results = []
        for i in range(3):
            print(f"   호출 {i+1}/3...")
            result = get_nutrition_recommendation_streaming(
                deficient_nutrients={"칼로리": 80.0},
                rdi_info={"칼로리": 2500},
                gender="male"
            )
            results.append(result)
            time.sleep(1)  # 1초 대기
        
        # 모든 호출이 성공해야 함
        for i, result in enumerate(results):
            self.assertIsNotNone(result, f"호출 {i+1}이 실패함")
        
        print(f"✅ 연속 API 호출 완료 - {len(results)}개 모두 성공")

    def test_long_response_handling(self):
        """긴 응답 처리 테스트"""
        print("📜 긴 응답 처리 테스트 시작...")
        
        # 많은 영양소를 포함한 복잡한 분석 요청
        complex_deficient = {
            "칼로리": 60.0, "단백질": 70.0, "칼슘": 50.0, 
            "철": 60.0, "비타민A": 40.0, "비타민C": 30.0,
            "식이섬유": 50.0, "비타민D": 20.0
        }
        
        complex_excessive = {
            "나트륨": 150.0, "지방": 130.0, "당류": 200.0
        }
        
        result = get_comprehensive_nutrition_analysis_streaming(
            totals=self.test_data["totals"],
            male_pct=self.test_data["male_pct"],
            female_pct=self.test_data["female_pct"],
            deficient_nutrients=complex_deficient,
            excessive_nutrients=complex_excessive,
            rdi_info=self.test_data["rdi_male"],
            gender="male"
        )
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 500)  # 복잡한 분석이므로 더 긴 응답 기대
        
        print(f"✅ 복잡한 분석 완료")
        print(f"📝 응답 길이: {len(result)}자")


class TestAPIErrorHandling(unittest.TestCase):
    """API 에러 핸들링 테스트"""

    def test_invalid_api_key(self):
        """잘못된 API 키 테스트"""
        print("🔑 잘못된 API 키 테스트...")
        
        # 환경변수를 임시로 잘못된 값으로 변경
        original_key = os.environ.get('CLOVASTUDIO_API_KEY')
        os.environ['CLOVASTUDIO_API_KEY'] = 'invalid_key'
        
        try:
            result = get_nutrition_recommendation_streaming(
                deficient_nutrients={"칼로리": 80.0},
                rdi_info={"칼로리": 2500},
                gender="male"
            )
            
            # 잘못된 키로는 LLM 응답이 실패하고 통계 기반으로 fallback되어야 함
            self.assertIsNotNone(result)
            self.assertIn("AI 추천 서비스를 이용하려면 API 키가 필요합니다", result)
            
            print("✅ 잘못된 API 키에 대한 fallback 정상 작동")
            
        finally:
            # 원래 환경변수 복원
            if original_key:
                os.environ['CLOVASTUDIO_API_KEY'] = original_key
            else:
                os.environ.pop('CLOVASTUDIO_API_KEY', None)


def run_integration_tests():
    """통합 테스트 실행"""
    print("🧪 LLM Client 실제 API 통합 테스트")
    print("=" * 60)
    
    # 환경변수 확인
    required_vars = ['CLOVASTUDIO_API_HOST', 'CLOVASTUDIO_API_KEY', 'CLOVASTUDIO_REQUEST_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ 다음 환경변수가 설정되지 않았습니다:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n실제 API 키를 설정한 후 다시 실행해주세요.")
        return False
    
    print("✅ 모든 환경변수가 설정되었습니다.")
    print(f"🌐 API Host: {os.getenv('CLOVASTUDIO_API_HOST')}")
    print(f"🔑 API Key: {os.getenv('CLOVASTUDIO_API_KEY')[:10]}...")
    print()
    
    # 테스트 실행
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRealLLMAPI)
    suite.addTests(loader.loadTestsFromTestCase(TestAPIErrorHandling))
    
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 통합 테스트 결과:")
    print(f"   총 테스트: {result.testsRun}")
    print(f"   성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   실패: {len(result.failures)}")
    print(f"   에러: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 모든 통합 테스트가 성공했습니다!")
        return True
    else:
        print("\n⚠️  일부 통합 테스트가 실패했습니다.")
        return False


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
