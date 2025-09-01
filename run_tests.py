#!/usr/bin/env python3
"""
LLM Client 테스트 실행 스크립트

사용법:
python run_tests.py                    # 모든 테스트 실행
python run_tests.py TestCompletionExecutor  # 특정 테스트 클래스만 실행
python run_tests.py -v                 # 상세 출력
"""

import sys
import unittest
import os
from datetime import datetime

def run_tests():
    """테스트 실행 함수"""
    print("🧪 NCP Daily Calories - LLM Client Unit Tests")
    print("=" * 60)
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python 버전: {sys.version}")
    print(f"📁 작업 디렉토리: {os.getcwd()}")
    print()

    # 환경변수 체크
    print("🔧 환경변수 상태:")
    env_vars = ['CLOVASTUDIO_API_HOST', 'CLOVASTUDIO_API_KEY', 'CLOVASTUDIO_REQUEST_ID']
    for var in env_vars:
        value = os.getenv(var)
        status = "✅ 설정됨" if value else "❌ 없음"
        print(f"   {var}: {status}")
    print()

    # 테스트 로더 설정
    loader = unittest.TestLoader()
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        if sys.argv[1] == '-v':
            verbosity = 2
            suite = loader.discover('.', pattern='test_llm_client.py')
        else:
            verbosity = 2
            # 특정 테스트 클래스 또는 메서드 실행
            try:
                suite = loader.loadTestsFromName(f'test_llm_client.{sys.argv[1]}')
            except AttributeError:
                print(f"❌ 테스트 '{sys.argv[1]}'를 찾을 수 없습니다.")
                return False
    else:
        verbosity = 2
        suite = loader.discover('.', pattern='test_llm_client.py')

    # 테스트 실행
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        buffer=True,
        stream=sys.stdout
    )
    
    print("🚀 테스트 시작...")
    print("-" * 60)
    
    result = runner.run(suite)
    
    print("-" * 60)
    print("📊 테스트 결과 요약:")
    print(f"   총 테스트: {result.testsRun}")
    print(f"   성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   실패: {len(result.failures)}")
    print(f"   에러: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"   - {test}")
    
    if result.errors:
        print("\n💥 에러가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"   - {test}")
    
    if result.wasSuccessful():
        print("\n🎉 모든 테스트가 성공했습니다!")
        return True
    else:
        print(f"\n⚠️  일부 테스트가 실패했습니다.")
        return False

def print_help():
    """도움말 출력"""
    print("""
🧪 LLM Client 테스트 실행 도구

사용법:
  python run_tests.py                           # 모든 테스트 실행
  python run_tests.py -v                        # 상세 출력 모드
  python run_tests.py TestCompletionExecutor    # 특정 테스트 클래스만 실행
  python run_tests.py TestLLMFunctions          # LLM 함수 테스트만 실행
  python run_tests.py TestEdgeCases             # 엣지 케이스 테스트만 실행
  python run_tests.py TestIntegration           # 통합 테스트만 실행
  python run_tests.py --help                    # 이 도움말 표시

테스트 클래스:
  - TestCompletionExecutor: CompletionExecutor 클래스 테스트
  - TestLLMFunctions: LLM API 호출 함수들 테스트
  - TestEdgeCases: 예외 상황 및 엣지 케이스 테스트
  - TestIntegration: 통합 테스트

환경변수 설정 (선택사항):
  - CLOVASTUDIO_API_HOST: Naver Cloud HyperCLOVA X API 호스트
  - CLOVASTUDIO_API_KEY: API 키
  - CLOVASTUDIO_REQUEST_ID: 요청 ID

참고:
  환경변수가 설정되지 않은 경우에도 통계 기반 fallback 테스트는 정상 실행됩니다.
""")

if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        sys.exit(0)
    
    success = run_tests()
    sys.exit(0 if success else 1)
