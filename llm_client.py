import os
import json
import requests
import time
import hashlib
from typing import Dict, List, Any

# 네이버클라우드 HyperCLOVA X LLM API 클라이언트
# test.py 구조를 기반으로 재작성

def generate_request_id():
    """현재 타임스탬프를 MD5 해시로 변환하여 request_id 생성"""
    timestamp = str(time.time())
    return hashlib.md5(timestamp.encode('utf-8')).hexdigest()

HOST = os.environ.get("NCP_LLM_HOST", "https://clovastudio.stream.ntruss.com")
API_KEY = os.environ.get("NCP_LLM_API_KEY", "")  # Bearer <api-key> 형태
REQUEST_ID = os.environ.get("NCP_REQUEST_ID", generate_request_id())

class CompletionExecutor:
    """test.py를 기반으로 한 완성도 높은 LLM 클라이언트"""
    
    def __init__(self, host, api_key, request_id):
        self._host = host
        self._api_key = api_key
        self._request_id = request_id
        

    def execute_streaming(self, completion_request, socketio=None, session_id=None):
        """스트리밍 방식으로 LLM 응답을 처리"""
        headers = {
            'Authorization': self._api_key,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'text/event-stream'
        }

        print(f"DEBUG: Making LLM request to {self._host + '/v3/chat-completions/HCX-005'}")
        print(f"DEBUG: Request data: {json.dumps(completion_request, ensure_ascii=False, indent=2)}")

        try:
            full_response = ""
            
            # 연결 중 메시지
            if socketio and session_id:
                socketio.emit('llm_response', {
                    'data': "🔗 AI 서버에 연결 중...", 
                    'type': 'connecting'
                }, room=session_id)
            
            with requests.post(self._host + '/v3/chat-completions/HCX-005',
                             headers=headers, json=completion_request, stream=True, timeout=30) as r:
                
                print(f"DEBUG: Response status: {r.status_code}")
                # print(f"DEBUG: Response status: {r.text}")
                
                if r.status_code != 200:
                    print(f"DEBUG: LLM API error status: {r.status_code}")
                    print(f"DEBUG: Response content: {r.text}")
                    # 에러 메시지 전송
                    if socketio and session_id:
                        socketio.emit('llm_response', {
                            'data': "❌ AI 서버 연결 오류", 
                            'type': 'error'
                        }, room=session_id)
                    return None
                
                # 응답 스트림 시작 메시지
                if socketio and session_id:
                    socketio.emit('llm_response', {
                        'data': "💭 AI가 응답을 생성하고 있습니다", 
                        'type': 'generating'
                    }, room=session_id)
                
                response_started = False
                for line in r.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        # print(f"DEBUG: Raw line: {line_str}")
                        
                        if line_str.startswith('data:'):
                            try:
                                json_str = line_str[5:]  # 'data:' 제거
                                if json_str.strip() == '[DONE]':
                                    print("DEBUG: Stream completed")
                                    break
                                    
                                json_data = json.loads(json_str)
                                # print(f"DEBUG: Parsed JSON: {json_data}")
                                
                                # 메시지 내용 추출
                                if 'message' in json_data and 'content' in json_data['message']:
                                    content = json_data['message']['content']
                                    if content:
                                        # 첫 번째 응답 시작 시 메시지 변경
                                        if not response_started:
                                            response_started = True
                                            print(f"DEBUG: First content received: {content[:50]}...")
                                            if socketio and session_id:
                                                socketio.emit('llm_response', {
                                                    'data': "✨ AI 영양사가 답변하고 있습니다...", 
                                                    'type': 'responding'
                                                }, room=session_id)
                                        
                                        full_response += content
                                        # print(f"DEBUG: Content chunk: {content}")  # 너무 많은 로그 방지
                                        
                                        # 실시간으로 소켓을 통해 전송
                                        if socketio and session_id:
                                            socketio.emit('llm_response', {
                                                'data': content, 
                                                'type': 'chunk',
                                                'full_response': full_response
                                            }, room=session_id)
                                else:
                                    print(f"DEBUG: Unexpected JSON structure: {json_data}")
                                            
                            except json.JSONDecodeError as e:
                                print(f"DEBUG: JSON decode error: {e}")
                                continue
                
                print(f"DEBUG: Full LLM response: {full_response}")
                print(f"DEBUG: Response length: {len(full_response) if full_response else 0}")
                
                # 응답이 있는지 확인
                if full_response and full_response.strip():
                    print("DEBUG: LLM returned valid response")
                    # 완료 신호 전송
                    if socketio and session_id:
                        socketio.emit('llm_response', {
                            'data': full_response, 
                            'type': 'complete'
                        }, room=session_id)
                    return full_response
                else:
                    print("DEBUG: LLM returned empty or invalid response")
                    return None
                
        except requests.exceptions.Timeout:
            print("DEBUG: LLM API timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: LLM API request error: {e}")
            return None
        except Exception as e:
            print(f"DEBUG: Unexpected error: {e}")
            return None

# 전역 클라이언트 인스턴스
llm_client = None
if API_KEY:
    # REQUEST_ID가 환경변수에 없으면 자동으로 타임스탬프 MD5 해시 생성
    request_id = REQUEST_ID if REQUEST_ID else generate_request_id()
    llm_client = CompletionExecutor(HOST, API_KEY, request_id)

def get_comprehensive_nutrition_analysis_streaming(totals: Dict[str, float], male_pct: Dict[str, float], female_pct: Dict[str, float], deficient_nutrients: Dict[str, float], excessive_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male", socketio=None, session_id=None):
    """
    전체 영양 분석 결과를 기반으로 종합적인 추천을 생성합니다.
    부족/과다 영양소를 모두 고려하여 한 번에 완전한 분석을 제공합니다.
    """
    if not llm_client:
        print("DEBUG: LLM client not available, using statistical recommendation")
        result = get_statistical_comprehensive_recommendation(deficient_nutrients, excessive_nutrients, rdi_info, gender)
        if socketio and session_id:
            socketio.emit('llm_response', {'data': result, 'type': 'complete'}, room=session_id)
        return result
    
    # 부족한 영양소 목록 생성
    deficient_list = []
    for nutrient, deficit in deficient_nutrients.items():
        nutrient_name = get_nutrient_korean_name(nutrient)
        rdi_amount = rdi_info.get(nutrient, 0)
        if rdi_amount > 0:
            current_amount = totals.get(nutrient, 0)
            percentage_current = round((current_amount / rdi_amount) * 100, 1)
            percentage_deficit = round((deficit / rdi_amount) * 100, 1)
            deficient_list.append(f"{nutrient_name} (현재 {percentage_current}%, {percentage_deficit}% 부족)")
    
    # 과다 섭취 영양소 목록 생성
    excessive_list = []
    for nutrient, excess in excessive_nutrients.items():
        nutrient_name = get_nutrient_korean_name(nutrient)
        rdi_amount = rdi_info.get(nutrient, 0)
        if rdi_amount > 0:
            current_amount = totals.get(nutrient, 0)
            percentage_current = round((current_amount / rdi_amount) * 100, 1)
            excessive_list.append(f"{nutrient_name} (현재 {percentage_current}%)")
    
    # 적정 수준 영양소 목록 생성
    optimal_list = []
    for nutrient, current_amount in totals.items():
        if nutrient in rdi_info and rdi_info[nutrient] > 0:
            if nutrient not in deficient_nutrients and nutrient not in excessive_nutrients:
                nutrient_name = get_nutrient_korean_name(nutrient)
                percentage_current = round((current_amount / rdi_info[nutrient]) * 100, 1)
                optimal_list.append(f"{nutrient_name} ({percentage_current}%)")
    
    # 성별 정보
    gender_info = {
        "male": "성인 남성(20-49세)",
        "female": "성인 여성(20-49세)"
    }
    
    gender_specific_advice = {
        "male": "남성의 근육량, 기초대사율, 활동량을 고려한",
        "female": "여성의 철분 필요량, 호르몬 변화, 임신/수유 가능성을 고려한"
    }
    
    # 종합 분석 프롬프트 생성
    prompt = f"""다음은 {gender_info[gender]}의 하루 영양소 섭취 분석 결과입니다:

📊 **영양소 상태 분석:**

🔴 **부족한 영양소 ({len(deficient_list)}개):**
{chr(10).join([f"• {item}" for item in deficient_list]) if deficient_list else "• 없음 (모든 영양소 충족)"}

⚠️ **과다 섭취 영양소 ({len(excessive_list)}개):**
{chr(10).join([f"• {item}" for item in excessive_list]) if excessive_list else "• 없음 (모든 영양소 적정 수준)"}

✅ **적정 수준 영양소 ({len(optimal_list)}개):**
{chr(10).join([f"• {item}" for item in optimal_list[:5]]) if optimal_list else "• 없음"}
{"..." if len(optimal_list) > 5 else ""}

🎯 **요청사항:**
{gender_specific_advice[gender]} 종합적인 영양 개선 방안을 제시해주세요.

**포함할 내용:**
1. **전체적인 영양 상태 평가** (한 줄 요약)
2. **우선순위별 개선 방안** (가장 중요한 것부터 3개)
3. **구체적인 식단 조정 방법** (추가할 음식, 줄일 음식)
4. **{gender_info[gender]} 맞춤 조언** (생활습관, 주의사항)
5. **실천 가능한 단계별 계획** (1주차, 2-4주차 목표)

**응답 형식:**
- 마크다운 문법을 사용해서 응답해주세요
- 제목은 ##, ### 등의 헤딩 태그 사용
- 중요한 내용은 **굵은 글씨** 강조
- 목록은 - 또는 1. 사용
- 음식명이나 영양소는 `코드 블록` 사용
- 필요시 표(table) 형식도 활용

한국인이 쉽게 구할 수 있는 음식 위주로 현실적이고 실천 가능한 방안을 제시해주세요."""

    # 진행 중 상태 표시를 위한 초기 메시지
    if socketio and session_id:
        socketio.emit('llm_response', {
            'data': "🤖 AI 영양사가 분석 중입니다.", 
            'type': 'thinking'
        }, room=session_id)

    # test.py와 동일한 요청 데이터 구조
    completion_request = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "너는 임상영양학을 전공한 영양박사야. 한국인의 식습관과 생활패턴을 잘 알고 있으며, 개인의 전체적인 영양 상태를 종합 분석하여 실용적이고 과학적인 맞춤형 조언을 제공한다. 모든 응답은 마크다운 문법을 사용해서 구조화된 형태로 제공한다."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 1000,
        "temperature": 0.5,
        "repetitionPenalty": 1.1,
        "stop": [],
        "seed": 0,
        "includeAiFilters": True
    }
    
    print(f"DEBUG: Calling LLM for comprehensive {gender} analysis")
    
    # test.py 기반 CompletionExecutor 사용
    result = llm_client.execute_streaming(completion_request, socketio, session_id)
    
    if result and result.strip():
        # LLM이 실제 내용이 있는 응답을 반환한 경우
        print(f"DEBUG: LLM success for {gender} - response length: {len(result)}")
        print(f"DEBUG: LLM response starts with: {result[:100]}...")
        return result
    else:
        print(f"DEBUG: LLM API failed or returned empty response for {gender}, falling back to statistical recommendation")
        print(f"DEBUG: Result was: {repr(result)}")
        fallback_result = get_statistical_comprehensive_recommendation(deficient_nutrients, excessive_nutrients, rdi_info, gender, is_fallback=True)
        if socketio and session_id:
            socketio.emit('llm_response', {'data': fallback_result, 'type': 'complete'}, room=session_id)
        return fallback_result


def get_nutrition_recommendation_streaming(deficient_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male", socketio=None, session_id=None):
    """
    스트리밍 방식으로 부족한 영양소 보충 추천을 생성합니다.
    test.py 기반 CompletionExecutor 사용
    """
    if not llm_client:
        print("DEBUG: LLM client not available, using statistical recommendation")
        result = get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
        if socketio and session_id:
            socketio.emit('llm_response', {'data': result, 'type': 'complete'}, room=session_id)
        return result
    
    # 부족한 영양소 목록 생성
    deficient_list = []
    for nutrient, deficit in deficient_nutrients.items():
        nutrient_name = get_nutrient_korean_name(nutrient)
        rdi_amount = rdi_info.get(nutrient, 0)
        if rdi_amount > 0:
            percentage_deficit = round((deficit / rdi_amount) * 100, 1)
            deficient_list.append(f"{nutrient_name} ({percentage_deficit}% 부족)")
    
    if not deficient_list:
        result = "현재 모든 영양소가 충분히 섭취되었습니다! 👍"
        if socketio and session_id:
            socketio.emit('llm_response', {'data': result, 'type': 'complete'}, room=session_id)
        return result
    
    # 성별에 따른 맞춤형 프롬프트 생성
    gender_info = {
        "male": "성인 남성(20-49세)",
        "female": "성인 여성(20-49세)"
    }
    
    gender_specific_advice = {
        "male": "남성의 근육량과 기초대사율을 고려한",
        "female": "여성의 철분 필요량과 호르몬 변화를 고려한"
    }
    
    # 프롬프트 생성
    prompt = f"""다음 영양소들이 {gender_info[gender]} 기준으로 부족합니다:
{', '.join(deficient_list)}

{gender_specific_advice[gender]} 부족한 영양소를 보충할 수 있는 음식이나 식품을 추천해주세요.
각 부족한 영양소에 대해 다음 정보를 포함해주세요:
1. 해당 영양소가 풍부한 음식들
2. {gender_info[gender]} 일일 권장 섭취량
3. 실생활에서 쉽게 실천할 수 있는 방법
4. {gender_info[gender]}에게 특히 중요한 이유

**응답 형식:**
- 마크다운 문법을 사용해서 응답해주세요
- 각 영양소별로 ### 제목 사용
- 음식명은 `코드 블록` 사용
- 중요한 내용은 **굵은 글씨** 강조
- 권장 섭취량은 표(table) 형식 활용

한국인이 쉽게 구할 수 있는 음식 위주로 추천해주세요."""

    # test.py와 동일한 요청 데이터 구조
    completion_request = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "너는 영양학을 전공한 영양박사야. 한국인의 식습관과 영양 상태를 잘 알고 있으며, 실용적이고 과학적인 영양 조언을 제공한다. 모든 응답은 마크다운 문법을 사용해서 구조화된 형태로 제공한다."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 1000,
        "temperature": 0.5,
        "repetitionPenalty": 1.1,
        "stop": [],
        "seed": 0,
        "includeAiFilters": True
    }
    
    print("DEBUG: Calling LLM for nutrition recommendation")
    
    # test.py 기반 CompletionExecutor 사용
    result = llm_client.execute_streaming(completion_request, socketio, session_id)
    
    if result and result.strip():
        # LLM이 실제 내용이 있는 응답을 반환한 경우
        return result
    else:
        print("DEBUG: LLM API failed or returned empty response, falling back to statistical recommendation")
        fallback_result = get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
        if socketio and session_id:
            socketio.emit('llm_response', {'data': fallback_result, 'type': 'complete'}, room=session_id)
        return fallback_result


def get_reduction_recommendation_streaming(excessive_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male", socketio=None, session_id=None):
    """
    스트리밍 방식으로 과다 섭취 영양소 감소 방법을 생성합니다.
    test.py 기반 CompletionExecutor 사용
    """
    if not llm_client:
        print("DEBUG: LLM client not available, using statistical recommendation")
        result = get_statistical_reduction_recommendation(excessive_nutrients, rdi_info, gender)
        if socketio and session_id:
            socketio.emit('llm_response', {'data': result, 'type': 'complete'}, room=session_id)
        return result
    
    # 과다 섭취한 영양소 목록 생성
    excessive_list = []
    for nutrient, excess in excessive_nutrients.items():
        nutrient_name = get_nutrient_korean_name(nutrient)
        rdi_amount = rdi_info.get(nutrient, 0)
        if rdi_amount > 0:
            percentage_excess = round((excess / rdi_amount) * 100, 1)
            excessive_list.append(f"{nutrient_name} ({percentage_excess}% 초과)")
    
    if not excessive_list:
        result = "현재 과다 섭취한 영양소가 없습니다! 👍"
        if socketio and session_id:
            socketio.emit('llm_response', {'data': result, 'type': 'complete'}, room=session_id)
        return result
    
    # 성별에 따른 맞춤형 프롬프트 생성
    gender_info = {
        "male": "성인 남성(20-49세)",
        "female": "성인 여성(20-49세)"
    }
    
    gender_specific_advice = {
        "male": "남성의 근육량과 기초대사율을 고려한",
        "female": "여성의 철분 필요량과 호르몬 변화를 고려한"
    }
    
    # 프롬프트 생성
    prompt = f"""다음 영양소들이 {gender_info[gender]} 기준으로 과다 섭취되었습니다:
{', '.join(excessive_list)}

{gender_specific_advice[gender]} 과다 섭취한 영양소를 효과적으로 줄일 수 있는 방법을 추천해주세요.
각 과다 영양소에 대해 다음 정보를 포함해주세요:
1. 줄여야 할 음식들
2. 대체할 수 있는 음식들
3. {gender_info[gender]} 적정 섭취량
4. 실생활에서 실천할 수 있는 구체적인 방법
5. {gender_info[gender]}에게 특히 주의해야 하는 이유

**응답 형식:**
- 마크다운 문법을 사용해서 응답해주세요
- 각 영양소별로 ### 제목 사용
- 줄여야 할 음식은 ❌ `음식명`
- 대체 음식은 ✅ `음식명`
- 중요한 주의사항은 **굵은 글씨** 강조
- 적정 섭취량은 표(table) 형식 활용

한국인이 쉽게 실천할 수 있는 현실적인 방법 위주로 추천해주세요."""

    # test.py와 동일한 요청 데이터 구조
    completion_request = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "너는 영양학을 전공한 영양박사야. 한국인의 식습관과 영양 상태를 잘 알고 있으며, 실용적이고 과학적인 영양 조언을 제공한다. 모든 응답은 마크다운 문법을 사용해서 구조화된 형태로 제공한다."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 1000,
        "temperature": 0.5,
        "repetitionPenalty": 1.1,
        "stop": [],
        "seed": 0,
        "includeAiFilters": True
    }
    
    print("DEBUG: Calling LLM for reduction recommendation")
    
    # test.py 기반 CompletionExecutor 사용
    result = llm_client.execute_streaming(completion_request, socketio, session_id)
    
    if result and result.strip():
        # LLM이 실제 내용이 있는 응답을 반환한 경우
        return result
    else:
        print("DEBUG: LLM API failed or returned empty response, falling back to statistical recommendation")
        fallback_result = get_statistical_reduction_recommendation(excessive_nutrients, rdi_info, gender)
        if socketio and session_id:
            socketio.emit('llm_response', {'data': fallback_result, 'type': 'complete'}, room=session_id)
        return fallback_result


# 기존 함수들 (비스트리밍, 호환성 유지)
def get_nutrition_recommendation(deficient_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male") -> str:
    """비스트리밍 버전 (호환성 유지)"""
    return get_nutrition_recommendation_streaming(deficient_nutrients, rdi_info, gender, None, None)

def get_reduction_recommendation(excessive_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male") -> str:
    """비스트리밍 버전 (호환성 유지)"""
    return get_reduction_recommendation_streaming(excessive_nutrients, rdi_info, gender, None, None)


# 영양소 한국어 이름 매핑
def get_nutrient_korean_name(nutrient_key: str) -> str:
    """영양소 키를 한국어 이름으로 변환 (포괄적 매핑)"""
    names = {
        # 기본 영양소
        'calories_kcal': '칼로리',
        'carbs_g': '탄수화물',
        'protein_g': '단백질',
        'fat_g': '지방',
        'saturated_fat_g': '포화지방',
        'trans_fat_g': '트랜스지방',
        'cholesterol_mg': '콜레스테롤',
        'sodium_mg': '나트륨',
        'potassium_mg': '칼륨',
        'fiber_g': '식이섬유',
        'sugars_g': '당류',
        'calcium_mg': '칼슘',
        'iron_mg': '철분',
        'phosphorus_mg': '인',
        'vitamin_a_ug': '비타민A',
        'thiamine_mg': '티아민',
        'riboflavin_mg': '리보플라빈',
        'niacin_mg': '나이아신',
        'vitamin_c_mg': '비타민C',
        
        # 다양한 형태의 키 매핑
        'sat_fat_g': '포화지방',
        'saturated_fat': '포화지방',
        'trans_fat': '트랜스지방',
        'dietary_fiber': '식이섬유',
        'total_sugars': '당류',
        'added_sugars': '첨가당',
        'vitamin_d': '비타민D',
        'vitamin_e': '비타민E',
        'vitamin_k': '비타민K',
        'folate': '엽산',
        'vitamin_b6': '비타민B6',
        'vitamin_b12': '비타민B12',
        'magnesium': '마그네슘',
        'zinc': '아연',
        'selenium': '셀레늄',
        
        # 영어 원문도 매핑
        'Calories': '칼로리',
        'Total Fat': '지방',
        'Saturated Fat': '포화지방',
        'Trans Fat': '트랜스지방',
        'Cholesterol': '콜레스테롤',
        'Sodium': '나트륨',
        'Total Carbohydrate': '탄수화물',
        'Dietary Fiber': '식이섬유',
        'Total Sugars': '당류',
        'Added Sugars': '첨가당',
        'Protein': '단백질',
        'Vitamin D': '비타민D',
        'Calcium': '칼슘',
        'Iron': '철분',
        'Potassium': '칼륨'
    }
    
    # 대소문자 구분 없이 매핑
    result = names.get(nutrient_key)
    if result:
        return result
    
    # 소문자로 변환해서 다시 시도
    result = names.get(nutrient_key.lower())
    if result:
        return result
        
    # 키에서 단위 제거 후 매핑 시도 (예: sat_fat_g -> sat_fat)
    key_without_unit = nutrient_key.replace('_g', '').replace('_mg', '').replace('_ug', '').replace('_kcal', '')
    result = names.get(key_without_unit)
    if result:
        return result
    
    # 매핑되지 않은 경우 원본 반환
    return nutrient_key


def calculate_deficient_nutrients(totals: Dict[str, float], rdi_info: Dict[str, float]) -> Dict[str, float]:
    """부족한 영양소 계산"""
    deficient = {}
    for nutrient, rdi_amount in rdi_info.items():
        if nutrient in totals and rdi_amount > 0:
            current_amount = totals[nutrient]
            if current_amount < rdi_amount:
                deficit = rdi_amount - current_amount
                deficient[nutrient] = deficit
    return deficient


def calculate_excessive_nutrients(totals: Dict[str, float], rdi_info: Dict[str, float]) -> Dict[str, float]:
    """과다 섭취 영양소 계산"""
    excessive = {}
    for nutrient, rdi_amount in rdi_info.items():
        if nutrient in totals and rdi_amount > 0:
            current_amount = totals[nutrient]
            # 권장량의 150% 이상을 과다로 판단
            excessive_threshold = rdi_amount * 1.5
            if current_amount > excessive_threshold:
                excess = current_amount - rdi_amount
                excessive[nutrient] = excess
    return excessive


# 통계 기반 추천 (API 없을 때 대체)
def get_statistical_nutrition_recommendation(deficient_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male", is_fallback: bool = True) -> str:
    """API 없을 때 통계 기반 추천"""
    if not deficient_nutrients:
        return "현재 모든 영양소가 충분히 섭취되었습니다! 👍"
    
    recommendations = []
    
    food_recommendations = {
        'calories_kcal': {
            'male': '견과류(아몬드, 호두), 아보카도, 바나나, 현미밥',
            'female': '견과류(아몬드, 호두), 아보카도, 바나나, 현미밥'
        },
        'protein_g': {
            'male': '닭가슴살, 달걀, 두부, 생선(연어, 고등어)',
            'female': '닭가슴살, 달걀, 두부, 생선(연어, 고등어)'
        },
        'carbs_g': {
            'male': '현미, 고구마, 귀리, 바나나',
            'female': '현미, 고구마, 귀리, 바나나'
        },
        'fat_g': {
            'male': '올리브오일, 견과류, 아보카도, 연어',
            'female': '올리브오일, 견과류, 아보카도, 연어'
        },
        'calcium_mg': {
            'male': '우유, 요거트, 치즈, 멸치, 시금치',
            'female': '우유, 요거트, 치즈, 멸치, 시금치'
        },
        'iron_mg': {
            'male': '시금치, 소고기, 닭고기, 콩류',
            'female': '시금치, 소고기, 닭고기, 콩류, 굴'
        },
        'sodium_mg': {
            'male': '김치, 된장, 간장 (적당량)',
            'female': '김치, 된장, 간장 (적당량)'
        },
        'vitamin_c_mg': {
            'male': '오렌지, 키위, 딸기, 브로콜리, 파프리카',
            'female': '오렌지, 키위, 딸기, 브로콜리, 파프리카'
        }
    }
    
    for nutrient in deficient_nutrients:
        nutrient_name = get_nutrient_korean_name(nutrient)
        if nutrient in food_recommendations:
            foods = food_recommendations[nutrient][gender]
            recommendations.append(f"• {nutrient_name}: {foods}")
    
    gender_text = "남성" if gender == "male" else "여성"
    
    if is_fallback:
        result = f"⚠️ AI 추천 서비스를 이용하려면 API 키가 필요합니다.\n\n📊 통계 기반 {gender_text} 맞춤 추천:\n\n" + "\n".join(recommendations)
        result += f"\n\n💡 {gender_text}에게 특히 중요한 영양소들을 위주로 선별된 음식들입니다."
    else:
        result = f"📊 {gender_text} 맞춤 영양 추천:\n\n" + "\n".join(recommendations)
        result += f"\n\n💡 {gender_text}에게 특히 중요한 영양소들을 위주로 선별된 음식들입니다."
    
    return result


def get_statistical_comprehensive_recommendation(deficient_nutrients: Dict[str, float], excessive_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male", is_fallback: bool = True) -> str:
    """종합적인 통계 기반 추천 (API 없을 때 대체)"""
    gender_text = "남성" if gender == "male" else "여성"
    
    if is_fallback:
        result = f"⚠️ AI 추천 서비스를 이용하려면 API 키가 필요합니다.\n\n📊 통계 기반 {gender_text} 종합 영양 분석:\n\n"
    else:
        result = f"📊 {gender_text} 종합 영양 분석:\n\n"
    
    # 전체적인 상태 평가
    total_issues = len(deficient_nutrients) + len(excessive_nutrients)
    if total_issues == 0:
        result += "🎉 **전체 평가:** 모든 영양소가 적정 수준으로 매우 양호한 상태입니다!\n\n"
    elif total_issues <= 3:
        result += f"✅ **전체 평가:** {total_issues}개 영양소에 주의가 필요하지만 전반적으로 양호한 상태입니다.\n\n"
    else:
        result += f"⚠️ **전체 평가:** {total_issues}개 영양소 개선이 필요하여 식단 조정을 권장합니다.\n\n"
    
    # 부족한 영양소 대응
    if deficient_nutrients:
        result += "🔴 **부족한 영양소 개선 방안:**\n"
        for nutrient in list(deficient_nutrients.keys())[:3]:  # 상위 3개만
            nutrient_name = get_nutrient_korean_name(nutrient)
            if nutrient == 'protein_g':
                foods = "닭가슴살, 달걀, 두부, 생선" if gender == "male" else "닭가슴살, 달걀, 두부, 콩류"
            elif nutrient == 'calcium_mg':
                foods = "우유, 멸치, 치즈, 시금치" if gender == "male" else "우유, 멸치, 치즈, 케일"
            elif nutrient == 'iron_mg':
                foods = "소고기, 시금치, 콩류" if gender == "male" else "소고기, 시금치, 굴, 콩류"
            elif nutrient == 'vitamin_c_mg':
                foods = "오렌지, 키위, 브로콜리, 파프리카"
            elif nutrient == 'fiber_g':
                foods = "현미, 고구마, 사과, 양배추"
            else:
                foods = "균형 잡힌 식단"
            result += f"• {nutrient_name}: {foods}\n"
        result += "\n"
    
    # 과다 영양소 대응
    if excessive_nutrients:
        result += "⚠️ **과다 섭취 영양소 조절 방안:**\n"
        for nutrient in list(excessive_nutrients.keys())[:3]:  # 상위 3개만
            nutrient_name = get_nutrient_korean_name(nutrient)
            if nutrient == 'sodium_mg':
                advice = "라면, 찌개류 줄이고 신선한 채소 늘리기"
            elif nutrient == 'saturated_fat_g':
                advice = "튀김, 버터 줄이고 올리브오일, 견과류로 대체"
            elif nutrient == 'sugars_g':
                advice = "음료수, 과자 줄이고 신선한 과일로 대체"
            else:
                advice = "섭취량 조절 및 균형 맞추기"
            result += f"• {nutrient_name}: {advice}\n"
        result += "\n"
    
    # 성별별 맞춤 조언
    if gender == "male":
        result += "👨 **남성 맞춤 조언:**\n"
        result += "• 근육량 유지를 위한 충분한 단백질 섭취\n"
        result += "• 활동량에 맞는 적절한 칼로리 조절\n"
        result += "• 규칙적인 운동과 함께 균형잡힌 식단 유지\n\n"
    else:
        result += "👩 **여성 맞춤 조언:**\n"
        result += "• 철분 부족 예방을 위한 철분 함유 식품 섭취\n"
        result += "• 골건강을 위한 칼슘, 비타민D 충분 섭취\n"
        result += "• 호르몬 균형을 위한 규칙적인 식사 패턴\n\n"
    
    if is_fallback:
        result += "💡 더 정확한 개인 맞춤 분석을 원하시면 AI 추천 서비스 이용을 권장합니다."
    else:
        result += "💡 지속적인 실천으로 건강한 영양 균형을 유지하세요."
    
    return result


def get_statistical_reduction_recommendation(excessive_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male", is_fallback: bool = True) -> str:
    """API 없을 때 통계 기반 감소 추천"""
    if not excessive_nutrients:
        return "현재 과다 섭취한 영양소가 없습니다! 👍"
    
    recommendations = []
    
    reduction_recommendations = {
        'sodium_mg': {
            'reduce': '라면, 찌개류, 김치, 젓갈류, 가공식품',
            'alternative': '신선한 채소, 과일, 허브 양념'
        },
        'saturated_fat_g': {
            'reduce': '버터, 치즈, 육류 지방, 튀김류',
            'alternative': '올리브오일, 견과류, 생선'
        },
        'sugars_g': {
            'reduce': '탄산음료, 과자, 케이크, 사탕',
            'alternative': '신선한 과일, 무가당 요거트'
        },
        'cholesterol_mg': {
            'reduce': '계란 노른자, 내장류, 새우',
            'alternative': '계란 흰자, 생선, 두부'
        }
    }
    
    for nutrient in excessive_nutrients:
        nutrient_name = get_nutrient_korean_name(nutrient)
        if nutrient in reduction_recommendations:
            reduce_foods = reduction_recommendations[nutrient]['reduce']
            alternative_foods = reduction_recommendations[nutrient]['alternative']
            recommendations.append(f"• {nutrient_name}:\n  - 줄일 음식: {reduce_foods}\n  - 대체 음식: {alternative_foods}")
    
    gender_text = "남성" if gender == "male" else "여성"
    
    if is_fallback:
        result = f"⚠️ AI 추천 서비스를 이용하려면 API 키가 필요합니다.\n\n📊 통계 기반 {gender_text} 맞춤 감소 방법:\n\n" + "\n\n".join(recommendations)
        result += f"\n\n💡 {gender_text} 건강을 위해 점진적으로 줄여나가세요."
    else:
        result = f"📊 {gender_text} 맞춤 감소 방법:\n\n" + "\n\n".join(recommendations)
        result += f"\n\n💡 {gender_text} 건강을 위해 점진적으로 줄여나가세요."
    
    return result