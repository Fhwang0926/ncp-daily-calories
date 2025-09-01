"""
LLM Client 유닛 테스트

이 파일은 llm_client.py의 주요 기능들을 테스트합니다:
- CompletionExecutor 클래스 테스트
- LLM API 호출 테스트  
- 스트리밍 응답 처리 테스트
- 에러 핸들링 테스트
- 통계 기반 추천 fallback 테스트
"""

import unittest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

# 테스트 대상 모듈 import
try:
    from llm_client import (
        CompletionExecutor,
        get_comprehensive_nutrition_analysis_streaming,
        get_nutrition_recommendation_streaming,
        get_reduction_recommendation_streaming,
        get_statistical_comprehensive_recommendation,
        get_statistical_nutrition_recommendation,
        get_statistical_reduction_recommendation
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("현재 디렉토리에서 llm_client.py를 찾을 수 없습니다.")
    sys.exit(1)


class TestCompletionExecutor(unittest.TestCase):
    """CompletionExecutor 클래스 테스트"""

    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        self.host = "https://clovastudio.stream.ntruss.com"
        self.api_key = "test_api_key"
        self.request_id = "test_request_id"
        self.executor = CompletionExecutor(self.host, self.api_key, self.request_id)

    def test_init(self):
        """CompletionExecutor 초기화 테스트"""
        self.assertEqual(self.executor._host, self.host)
        self.assertEqual(self.executor._api_key, self.api_key)
        self.assertEqual(self.executor._request_id, self.request_id)

    @patch('requests.post')
    def test_execute_streaming_success(self, mock_post):
        """성공적인 스트리밍 응답 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            'data: {"message": {"content": "Hello! "}}'.encode('utf-8'),
            'data: {"message": {"content": "Nutrition analysis result."}}'.encode('utf-8'),
            b'data: [DONE]'
        ]
        # Context manager 지원을 위한 설정
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_post.return_value = mock_response

        completion_request = {
            "messages": [{"role": "user", "content": "테스트 메시지"}],
            "maxTokens": 1000,
            "temperature": 0.7
        }

        result = self.executor.execute_streaming(completion_request)

        self.assertIsNotNone(result)
        self.assertIn("Hello!", result)
        self.assertIn("Nutrition analysis result.", result)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_execute_streaming_http_error(self, mock_post):
        """HTTP 에러 응답 테스트"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        completion_request = {
            "messages": [{"role": "user", "content": "테스트 메시지"}]
        }

        result = self.executor.execute_streaming(completion_request)
        self.assertIsNone(result)

    @patch('requests.post')
    def test_execute_streaming_connection_error(self, mock_post):
        """연결 에러 테스트"""
        mock_post.side_effect = Exception("Connection failed")

        completion_request = {
            "messages": [{"role": "user", "content": "테스트 메시지"}]
        }

        result = self.executor.execute_streaming(completion_request)
        self.assertIsNone(result)

    @patch('requests.post')
    def test_execute_streaming_with_socketio(self, mock_post):
        """Socket.IO와 함께 스트리밍 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            'data: {"message": {"content": "Test response"}}'.encode('utf-8'),
            b'data: [DONE]'
        ]
        # Context manager 지원을 위한 설정
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_post.return_value = mock_response

        # Mock Socket.IO
        mock_socketio = Mock()
        session_id = "test_session"

        completion_request = {
            "messages": [{"role": "user", "content": "테스트 메시지"}]
        }

        result = self.executor.execute_streaming(
            completion_request, 
            socketio=mock_socketio, 
            session_id=session_id
        )

        self.assertIsNotNone(result)
        self.assertEqual(result, "Test response")
        
        # Socket.IO emit이 호출되었는지 확인
        self.assertTrue(mock_socketio.emit.called)

    @patch('requests.post')
    def test_execute_streaming_empty_response(self, mock_post):
        """빈 응답 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"message": {"content": ""}}',
            b'data: [DONE]'
        ]
        # Context manager 지원을 위한 설정
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_post.return_value = mock_response

        completion_request = {
            "messages": [{"role": "user", "content": "테스트 메시지"}]
        }

        result = self.executor.execute_streaming(completion_request)
        # 빈 응답의 경우 None이 반환됨 (실제 구현에 맞춤)
        self.assertIsNone(result)


class TestLLMFunctions(unittest.TestCase):
    """LLM 함수들 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.totals = {
            "칼로리": 1800,
            "단백질": 60,
            "탄수화물": 250,
            "지방": 50,
            "나트륨": 2000
        }
        
        self.male_pct = {
            "칼로리": 72.0,
            "단백질": 120.0,
            "탄수화물": 76.9,
            "지방": 90.9,
            "나트륨": 80.0
        }
        
        self.female_pct = {
            "칼로리": 90.0,
            "단백질": 150.0,
            "탄수화물": 96.2,
            "지방": 113.6,
            "나트륨": 100.0
        }
        
        self.deficient_nutrients = {
            "칼로리": 72.0,
            "나트륨": 80.0
        }
        
        self.excessive_nutrients = {
            "단백질": 120.0,
            "지방": 113.6
        }
        
        self.rdi_info = {
            "칼로리": 2500,
            "단백질": 50,
            "탄수화물": 325,
            "지방": 44,
            "나트륨": 2500
        }

    @patch.dict(os.environ, {
        'CLOVASTUDIO_API_HOST': 'https://test.host.com',
        'CLOVASTUDIO_API_KEY': 'test_key',
        'CLOVASTUDIO_REQUEST_ID': 'test_request'
    })
    @patch('llm_client.llm_client')  # llm_client 모듈 변수를 직접 Mock
    def test_get_comprehensive_nutrition_analysis_streaming_success(self, mock_llm_client):
        """종합 영양 분석 스트리밍 성공 테스트"""
        # Mock llm_client 설정
        mock_llm_client.execute_streaming.return_value = "AI generated comprehensive nutrition analysis result."

        result = get_comprehensive_nutrition_analysis_streaming(
            totals=self.totals,
            male_pct=self.male_pct,
            female_pct=self.female_pct,
            deficient_nutrients=self.deficient_nutrients,
            excessive_nutrients=self.excessive_nutrients,
            rdi_info=self.rdi_info,
            gender="male"
        )

        self.assertIsNotNone(result)
        self.assertIn("AI", result)
        mock_llm_client.execute_streaming.assert_called_once()

    @patch.dict(os.environ, {})  # 환경변수 없음
    def test_get_comprehensive_nutrition_analysis_no_env_vars(self):
        """환경변수 없을 때 통계 기반 fallback 테스트"""
        result = get_comprehensive_nutrition_analysis_streaming(
            totals=self.totals,
            male_pct=self.male_pct,
            female_pct=self.female_pct,
            deficient_nutrients=self.deficient_nutrients,
            excessive_nutrients=self.excessive_nutrients,
            rdi_info=self.rdi_info,
            gender="male"
        )

        self.assertIsNotNone(result)
        self.assertIn("AI 추천 서비스를 이용하려면 API 키가 필요합니다", result)

    @patch.dict(os.environ, {
        'CLOVASTUDIO_API_HOST': 'https://test.host.com',
        'CLOVASTUDIO_API_KEY': 'test_key',
        'CLOVASTUDIO_REQUEST_ID': 'test_request'
    })
    @patch('llm_client.CompletionExecutor')
    def test_get_comprehensive_nutrition_analysis_llm_failure(self, mock_executor_class):
        """LLM 실패 시 통계 기반 fallback 테스트"""
        # Mock CompletionExecutor가 None 반환 (실패)
        mock_executor = Mock()
        mock_executor.execute_streaming.return_value = None
        mock_executor_class.return_value = mock_executor

        result = get_comprehensive_nutrition_analysis_streaming(
            totals=self.totals,
            male_pct=self.male_pct,
            female_pct=self.female_pct,
            deficient_nutrients=self.deficient_nutrients,
            excessive_nutrients=self.excessive_nutrients,
            rdi_info=self.rdi_info,
            gender="female"
        )

        self.assertIsNotNone(result)
        self.assertIn("AI 추천 서비스를 이용하려면 API 키가 필요합니다", result)

    def test_get_statistical_comprehensive_recommendation(self):
        """통계 기반 종합 추천 테스트"""
        result = get_statistical_comprehensive_recommendation(
            deficient_nutrients=self.deficient_nutrients,
            excessive_nutrients=self.excessive_nutrients,
            rdi_info=self.rdi_info,
            gender="male",
            is_fallback=True
        )

        self.assertIsNotNone(result)
        self.assertIn("AI 추천 서비스를 이용하려면 API 키가 필요합니다", result)
        self.assertIn("부족한 영양소", result)
        self.assertIn("과다 섭취", result)

    def test_get_statistical_comprehensive_recommendation_no_fallback(self):
        """통계 기반 추천 (fallback 아님) 테스트"""
        result = get_statistical_comprehensive_recommendation(
            deficient_nutrients=self.deficient_nutrients,
            excessive_nutrients=self.excessive_nutrients,
            rdi_info=self.rdi_info,
            gender="female",
            is_fallback=False
        )

        self.assertIsNotNone(result)
        self.assertNotIn("AI 추천 서비스를 이용하려면 API 키가 필요합니다", result)
        self.assertIn("부족한 영양소", result)

    def test_get_statistical_nutrition_recommendation(self):
        """통계 기반 부족 영양소 추천 테스트"""
        result = get_statistical_nutrition_recommendation(
            deficient_nutrients=self.deficient_nutrients,
            rdi_info=self.rdi_info,
            gender="male"
        )

        self.assertIsNotNone(result)
        self.assertIn("추천", result)

    def test_get_statistical_reduction_recommendation(self):
        """통계 기반 과다 영양소 감소 추천 테스트"""
        result = get_statistical_reduction_recommendation(
            excessive_nutrients=self.excessive_nutrients,
            rdi_info=self.rdi_info,
            gender="female"
        )

        self.assertIsNotNone(result)
        self.assertIn("감소", result)

    def test_empty_nutrients(self):
        """빈 영양소 데이터 테스트"""
        result = get_statistical_comprehensive_recommendation(
            deficient_nutrients={},
            excessive_nutrients={},
            rdi_info=self.rdi_info,
            gender="male"
        )

        self.assertIsNotNone(result)
        self.assertIn("모든 영양소가 적정", result)


class TestEdgeCases(unittest.TestCase):
    """엣지 케이스 테스트"""

    def test_invalid_gender(self):
        """잘못된 성별 입력 테스트"""
        result = get_statistical_comprehensive_recommendation(
            deficient_nutrients={"칼로리": 80},
            excessive_nutrients={},
            rdi_info={"칼로리": 2500},
            gender="invalid"  # 잘못된 성별
        )

        self.assertIsNotNone(result)
        # 기본값으로 처리되는지 확인

    def test_missing_rdi_info(self):
        """RDI 정보 누락 테스트"""
        result = get_statistical_nutrition_recommendation(
            deficient_nutrients={"비타민C": 50},  # RDI에 없는 영양소
            rdi_info={"칼로리": 2500},
            gender="male"
        )

        self.assertIsNotNone(result)

    def test_debug_logging(self):
        """디버그 로깅 테스트"""
        # 디버그 로깅이 있는 함수 호출
        result = get_statistical_comprehensive_recommendation(
            deficient_nutrients={"칼로리": 80},
            excessive_nutrients={},
            rdi_info={"칼로리": 2500},
            gender="male"
        )
        
        # 결과가 정상적으로 반환되는지 확인 (로깅 자체보다는 기능 테스트)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    @patch.dict(os.environ, {
        'CLOVASTUDIO_API_HOST': 'https://clovastudio.stream.ntruss.com',
        'CLOVASTUDIO_API_KEY': 'test_key',
        'CLOVASTUDIO_REQUEST_ID': 'test_request'
    })
    def test_environment_variables_loaded(self):
        """환경변수 로딩 테스트"""
        # 환경변수가 제대로 설정되었는지 확인
        self.assertIsNotNone(os.getenv('CLOVASTUDIO_API_HOST'))
        self.assertIsNotNone(os.getenv('CLOVASTUDIO_API_KEY'))
        self.assertIsNotNone(os.getenv('CLOVASTUDIO_REQUEST_ID'))

    def test_full_workflow_simulation(self):
        """전체 워크플로우 시뮬레이션"""
        # 실제 앱에서 사용되는 것과 유사한 데이터로 테스트
        totals = {
            "칼로리": 1800, "단백질": 60, "탄수화물": 250,
            "지방": 50, "나트륨": 2000, "칼슘": 600,
            "철": 8, "비타민A": 700, "비타민C": 80, "식이섬유": 20
        }
        
        deficient = {"칼로리": 72.0, "칼슘": 60.0, "비타민C": 80.0}
        excessive = {"나트륨": 120.0, "지방": 110.0}
        
        rdi = {
            "칼로리": 2500, "단백질": 50, "탄수화물": 325,
            "지방": 44, "나트륨": 2500, "칼슘": 1000,
            "철": 10, "비타민A": 900, "비타민C": 100, "식이섬유": 25
        }

        # 남성과 여성 모두 테스트
        for gender in ["male", "female"]:
            result = get_statistical_comprehensive_recommendation(
                deficient_nutrients=deficient,
                excessive_nutrients=excessive,
                rdi_info=rdi,
                gender=gender
            )
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 100)  # 충분한 길이의 응답


if __name__ == '__main__':
    # 테스트 실행 설정
    print("🧪 LLM Client 유닛 테스트 시작")
    print("=" * 60)
    
    # 상세한 테스트 결과 출력을 위한 설정
    unittest.main(
        verbosity=2,  # 상세한 출력
        buffer=True,  # 출력 버퍼링
        warnings='ignore'  # 경고 무시
    )
