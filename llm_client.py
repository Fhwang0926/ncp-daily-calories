import os
import json
import requests
from typing import Dict, List, Any

# 네이버클라우드 HyperCLOVA X LLM API 클라이언트
# 실제 엔드포인트/API 키는 콘솔에서 발급받은 값으로 변경하세요.

HOST = os.environ.get("NCP_LLM_HOST", "https://clovastudio.stream.ntruss.com")
API_KEY = os.environ.get("NCP_LLM_API_KEY", "")  # Bearer <api-key> 형태
REQUEST_ID = os.environ.get("NCP_REQUEST_ID", "")

def get_nutrition_recommendation_streaming(deficient_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male", socketio=None, session_id=None):
    """
    스트리밍 방식으로 부족한 영양소 보충 추천을 생성합니다.
    """
    if not API_KEY or not API_KEY.strip():
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

{gender_specific_advice[gender]} 부족한 영양소를 효과적으로 보충할 수 있는 음식이나 식품을 추천해주세요. 
각 추천 음식에 대해 다음 정보를 포함해주세요:
1. 음식명
2. 보충할 수 있는 주요 영양소
3. {gender_info[gender]} 권장 섭취량
4. 간단한 조리법이나 섭취 방법
5. {gender_info[gender]}에게 특히 중요한 이유

한국인이 쉽게 구할 수 있고 일상적으로 섭취할 수 있는 음식 위주로 추천해주세요."""

    headers = {
        "Authorization": API_KEY,
        "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "text/event-stream"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": "너는 영양학을 전공한 영양박사야. 한국인의 식습관과 영양 상태를 잘 알고 있으며, 실용적이고 과학적인 영양 조언을 제공한다."}]},
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
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
    
    print(f"DEBUG: Making streaming request to {HOST + '/v3/chat-completions/HCX-005'}")
    
    try:
        response = requests.post(
            HOST + '/v3/chat-completions/HCX-005',
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        print(f"DEBUG: Response status: {response.status_code}")
        
        if response.status_code == 200:
            # 스트리밍 응답 처리
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            json_data = json.loads(line_str[6:])  # 'data: ' 제거
                            if 'message' in json_data and 'content' in json_data['message']:
                                content = json_data['message']['content']
                                full_response += content
                                
                                # 실시간으로 소켓을 통해 전송
                                if socketio and session_id:
                                    socketio.emit('llm_response', {
                                        'data': content, 
                                        'type': 'chunk',
                                        'full_response': full_response
                                    }, room=session_id)
                                    
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: JSON decode error: {e}")
                            continue
            
            print(f"DEBUG: Full response: {full_response}")
            
            # 완료 신호 전송
            if socketio and session_id:
                socketio.emit('llm_response', {
                    'data': full_response, 
                    'type': 'complete'
                }, room=session_id)
                
            return full_response if full_response else "추천 정보를 가져올 수 없습니다."
        else:
            error_text = response.text
            print(f"DEBUG: Error response: {error_text}")
            print("DEBUG: LLM API error, falling back to statistical recommendation")
            result = get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
            if socketio and session_id:
                socketio.emit('llm_response', {'data': result, 'type': 'complete'}, room=session_id)
            return result
            
    except requests.exceptions.Timeout:
        print("DEBUG: LLM API timeout, falling back to statistical recommendation")
        result = get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
        if socketio and session_id:
            socketio.emit('llm_response', {'data': result, 'type': 'complete'}, room=session_id)
        return result
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: LLM API error: {str(e)}, falling back to statistical recommendation")
        result = get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
        if socketio and session_id:
            socketio.emit('llm_response', {'data': result, 'type': 'complete'}, room=session_id)
        return result
    except Exception as e:
        result = f"⚠️ 오류 발생: {str(e)}"
        if socketio and session_id:
            socketio.emit('llm_response', {'data': result, 'type': 'error'}, room=session_id)
        return result


def get_nutrition_recommendation(deficient_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male") -> str:
    """
    부족한 영양소를 보충하기 위한 음식 추천을 LLM에 요청합니다.
    API가 없거나 에러 시 통계 기반 추천을 제공합니다.
    
    Args:
        deficient_nutrients: 부족한 영양소와 부족량 정보
        rdi_info: 일일 권장량 정보
        gender: 성별 ("male" 또는 "female")
    
    Returns:
        LLM 또는 통계 기반 추천 결과
    """
    print(f"DEBUG: API_KEY exists: {bool(API_KEY)}")
    print(f"DEBUG: HOST: {HOST}")
    print(f"DEBUG: REQUEST_ID: {REQUEST_ID}")
    print(f"DEBUG: Deficient nutrients: {deficient_nutrients}")
    
    # API 키가 없거나 빈 경우 통계 기반 추천으로 대체
    if not API_KEY or not API_KEY.strip():
        return get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
    
    # 부족한 영양소 목록 생성
    deficient_list = []
    for nutrient, deficit in deficient_nutrients.items():
        nutrient_name = get_nutrient_korean_name(nutrient)
        rdi_amount = rdi_info.get(nutrient, 0)
        if rdi_amount > 0:
            percentage_deficit = round((deficit / rdi_amount) * 100, 1)
            deficient_list.append(f"{nutrient_name} ({percentage_deficit}% 부족)")
    
    if not deficient_list:
        return "현재 모든 영양소가 충분히 섭취되었습니다! 👍"
    
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

{gender_specific_advice[gender]} 부족한 영양소를 효과적으로 보충할 수 있는 음식이나 식품을 추천해주세요. 
각 추천 음식에 대해 다음 정보를 포함해주세요:
1. 음식명
2. 보충할 수 있는 주요 영양소
3. {gender_info[gender]} 권장 섭취량
4. 간단한 조리법이나 섭취 방법
5. {gender_info[gender]}에게 특히 중요한 이유

한국인이 쉽게 구할 수 있고 일상적으로 섭취할 수 있는 음식 위주로 추천해주세요."""

    headers = {
        "Authorization": API_KEY,
        "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "text/event-stream"
    }
    
    data = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "너는 영양학을 전공한 영양박사야. 사람 나이대별로 섭취 칼로리에 따른 피드백을 제일 잘해. 예시로 나트륨이 부족한 사람은 간장 요리, 간장 게장과 같은 필요 음식이나 식품을 추천을 잘해."
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
    
    print(f"DEBUG: Making request to {HOST + '/v3/chat-completions/HCX-005'}")
    print(f"DEBUG: Headers: {headers}")
    
    try:
        response = requests.post(
            HOST + '/v3/chat-completions/HCX-005',
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        print(f"DEBUG: Response status: {response.status_code}")
        
        if response.status_code == 200:
            # 스트리밍 응답 처리
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    # print(f"DEBUG: Response line: {line_str}")
                    if line_str.startswith('data: '):
                        try:
                            json_data = json.loads(line_str[6:])  # 'data: ' 제거
                            if 'message' in json_data and 'content' in json_data['message']:
                                full_response += json_data['message']['content']
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: JSON decode error: {e}")
                            continue
            
            print(f"DEBUG: Full response: {full_response}")
            return full_response if full_response else "추천 정보를 가져올 수 없습니다."
        else:
            error_text = response.text
            print(f"DEBUG: Error response: {error_text}")
            print("DEBUG: LLM API error, falling back to statistical recommendation")
            return get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
            
    except requests.exceptions.Timeout:
        print("DEBUG: LLM API timeout, falling back to statistical recommendation")
        return get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: LLM API error: {str(e)}, falling back to statistical recommendation")
        return get_statistical_nutrition_recommendation(deficient_nutrients, rdi_info, gender)
    except Exception as e:
        return f"⚠️ 오류 발생: {str(e)}"


def get_nutrient_korean_name(nutrient_key: str) -> str:
    """영양소 키를 한국어 이름으로 변환"""
    name_mapping = {
        "calories_kcal": "열량",
        "sodium_mg": "나트륨", 
        "carbs_g": "탄수화물",
        "sugars_g": "당류",
        "fat_g": "지방",
        "sat_fat_g": "포화지방",
        "trans_fat_g": "트랜스지방", 
        "cholesterol_mg": "콜레스테롤",
        "protein_g": "단백질",
        "total_volume_g": "내용량(g)",
        "total_volume_ml": "내용량(ml)"
    }
    return name_mapping.get(nutrient_key, nutrient_key)


def calculate_deficient_nutrients(totals: Dict[str, float], rdi: Dict[str, float], threshold: float = 0.8) -> Dict[str, float]:
    """
    부족한 영양소를 계산합니다.
    
    Args:
        totals: 현재 섭취한 영양소
        rdi: 일일 권장량
        threshold: 부족 판단 기준 (80% 미만을 부족으로 판단)
    
    Returns:
        부족한 영양소와 부족량
    """
    deficient = {}
    
    for nutrient, current_amount in totals.items():
        if nutrient in rdi and rdi[nutrient] > 0 and current_amount is not None:
            required_amount = rdi[nutrient] * threshold
            if current_amount < required_amount:
                deficit = required_amount - current_amount
                deficient[nutrient] = deficit
    
    return deficient


def calculate_excessive_nutrients(totals: Dict[str, float], rdi: Dict[str, float], threshold: float = 1.2) -> Dict[str, float]:
    """
    과다 섭취한 영양소를 계산합니다.
    
    Args:
        totals: 현재 섭취한 영양소
        rdi: 일일 권장량
        threshold: 과다 판단 기준 (120% 초과를 과다로 판단)
    
    Returns:
        과다 섭취한 영양소와 초과량
    """
    excessive = {}
    
    for nutrient, current_amount in totals.items():
        if nutrient in rdi and rdi[nutrient] > 0 and current_amount is not None:
            max_recommended = rdi[nutrient] * threshold
            if current_amount > max_recommended:
                excess = current_amount - max_recommended
                excessive[nutrient] = excess
    
    return excessive


def get_reduction_recommendation(excessive_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male") -> str:
    """
    과다 섭취한 영양소를 줄이기 위한 방법을 LLM에 요청합니다.
    API가 없거나 에러 시 통계 기반 감소 방법을 제공합니다.
    
    Args:
        excessive_nutrients: 과다 섭취한 영양소와 초과량 정보
        rdi_info: 일일 권장량 정보
        gender: 성별 ("male" 또는 "female")
    
    Returns:
        LLM 또는 통계 기반 감소 방법
    """
    # API 키가 없거나 빈 경우 통계 기반 추천으로 대체
    if not API_KEY or not API_KEY.strip():
        return get_statistical_reduction_recommendation(excessive_nutrients, rdi_info, gender)
    
    # 과다 섭취한 영양소 목록 생성
    excessive_list = []
    for nutrient, excess in excessive_nutrients.items():
        nutrient_name = get_nutrient_korean_name(nutrient)
        rdi_amount = rdi_info.get(nutrient, 0)
        if rdi_amount > 0:
            percentage_excess = round((excess / rdi_amount) * 100, 1)
            excessive_list.append(f"{nutrient_name} ({percentage_excess}% 초과)")
    
    if not excessive_list:
        return "현재 과다 섭취한 영양소가 없습니다! 👍"
    
    # 프롬프트 생성
    prompt = f"""다음 영양소들을 과다 섭취했습니다:
{', '.join(excessive_list)}

이러한 과다 섭취한 영양소를 줄이기 위한 방법을 알려주세요. 
각 영양소에 대해 다음 정보를 포함해주세요:
1. 과다 섭취 시 건강에 미치는 영향
2. 줄여야 할 음식이나 식품의 종류
3. 대체할 수 있는 건강한 음식
4. 일상생활에서 실천할 수 있는 구체적인 방법

한국인의 식습관을 고려한 실용적인 조언을 해주세요."""

    headers = {
        "Authorization": API_KEY,
        "X-NCP-CLOVASTUDIO-REQUEST-ID": REQUEST_ID,
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "text/event-stream"
    }
    
    data = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "너는 영양학을 전공한 영양박사야. 사용자가 과다 섭취한 영양소를 줄일 수 있는 실용적이고 안전한 방법을 제안해주세요."
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
    
    try:
        response = requests.post(
            HOST + '/v3/chat-completions/HCX-005',
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            # 스트리밍 응답 처리
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            json_data = json.loads(line_str[6:])  # 'data: ' 제거
                            if 'message' in json_data and 'content' in json_data['message']:
                                full_response += json_data['message']['content']
                        except json.JSONDecodeError:
                            continue
            
            return full_response if full_response else "감소 방법 정보를 가져올 수 없습니다."
        else:
            print(f"DEBUG: LLM API error for reduction, falling back to statistical recommendation")
            return get_statistical_reduction_recommendation(excessive_nutrients, rdi_info, gender)
            
    except requests.exceptions.Timeout:
        print("DEBUG: LLM API timeout for reduction, falling back to statistical recommendation")
        return get_statistical_reduction_recommendation(excessive_nutrients, rdi_info, gender)
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: LLM API error for reduction: {str(e)}, falling back to statistical recommendation")
        return get_statistical_reduction_recommendation(excessive_nutrients, rdi_info, gender)
    except Exception as e:
        return f"⚠️ 오류 발생: {str(e)}"


def get_statistical_nutrition_recommendation(deficient_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male") -> str:
    """
    통계 기반으로 부족한 영양소 보충 음식을 추천합니다.
    LLM API가 없거나 에러가 발생한 경우의 대안 방법입니다.
    """
    if not deficient_nutrients:
        return "현재 모든 영양소가 충분히 섭취되었습니다! 👍"
    
    # 영양소별 음식 매칭 데이터베이스
    nutrition_foods = {
        'calories_kcal': ['밥', '빵', '견과류', '오일'],
        'protein_g': ['계란', '닭가슴살', '두부', '콩류', '생선'],
        'carbs_g': ['밥', '고구마', '바나나', '오트밀', '현미'],
        'fat_g': ['견과류', '아보카도', '올리브오일', '연어'],
        'fiber_g': ['현미', '오트밀', '사과', '브로콜리', '콩류'],
        'sodium_mg': ['김치', '된장', '간장', '젓갈류'],
        'potassium_mg': ['바나나', '감자', '시금치', '아보카도'],
        'calcium_mg': ['우유', '치즈', '멸치', '브로콜리', '참깨'],
        'iron_mg': ['시금치', '간', '굴', '소고기', '콩류'],
        'vitamin_a_ug': ['당근', '고구마', '시금치', '간', '달걀'],
        'vitamin_c_mg': ['오렌지', '키위', '브로콜리', '딸기', '토마토'],
        'thiamine_mg': ['돼지고기', '현미', '콩류', '견과류'],
        'riboflavin_mg': ['우유', '계란', '간', '아몬드'],
        'niacin_mg': ['닭고기', '참치', '버섯', '땅콩'],
        'phosphorus_mg': ['생선', '유제품', '견과류', '콩류']
    }
    
    gender_info = "성인 남성" if gender == "male" else "성인 여성"
    
    recommendation_parts = []
    recommendation_parts.append("🔍 **AI 키가 설정되지 않아 통계 기반으로 추천을 제공합니다**")
    recommendation_parts.append("")
    recommendation_parts.append(f"📊 **{gender_info} 기준 부족한 영양소 보충 방법:**")
    recommendation_parts.append("")
    
    for nutrient, deficit in deficient_nutrients.items():
        nutrient_name = get_nutrient_korean_name(nutrient)
        rdi_amount = rdi_info.get(nutrient, 0)
        
        if rdi_amount > 0:
            percentage_deficit = round((deficit / rdi_amount) * 100, 1)
            foods = nutrition_foods.get(nutrient, ['균형잡힌 식품'])
            
            recommendation_parts.append(f"**{nutrient_name}** ({percentage_deficit}% 부족)")
            recommendation_parts.append(f"• 추천 음식: {', '.join(foods[:3])}")
            if gender == "female" and nutrient in ['iron_mg', 'calcium_mg']:
                recommendation_parts.append(f"• {gender_info}에게 특히 중요한 영양소입니다")
            elif gender == "male" and nutrient in ['protein_g', 'calories_kcal']:
                recommendation_parts.append(f"• {gender_info}의 높은 기초대사율을 고려하여 충분히 섭취하세요")
            recommendation_parts.append("")
    
    recommendation_parts.append("💡 **일반적인 조언:**")
    recommendation_parts.append("• 균형잡힌 식사를 통해 다양한 영양소를 섭취하세요")
    recommendation_parts.append("• 가공식품보다는 자연식품을 선택하세요")
    recommendation_parts.append("• 충분한 수분 섭취도 중요합니다")
    
    return "\n".join(recommendation_parts)


def get_statistical_reduction_recommendation(excessive_nutrients: Dict[str, float], rdi_info: Dict[str, float], gender: str = "male") -> str:
    """
    통계 기반으로 과다 섭취한 영양소 감소 방법을 추천합니다.
    LLM API가 없거나 에러가 발생한 경우의 대안 방법입니다.
    """
    if not excessive_nutrients:
        return "현재 과다 섭취한 영양소가 없습니다! 👍"
    
    # 영양소별 감소 방법 데이터베이스
    reduction_advice = {
        'sodium_mg': {
            'foods_to_reduce': ['라면', '김치', '젓갈', '가공식품', '패스트푸드'],
            'alternatives': ['신선한 채소', '무염 견과류', '허브 양념'],
            'tips': ['음식을 만들 때 소금 대신 허브나 향신료 사용', '가공식품 섭취 줄이기']
        },
        'fat_g': {
            'foods_to_reduce': ['튀김류', '삼겹살', '버터', '마요네즈'],
            'alternatives': ['구이나 찜 요리', '올리브오일', '아보카도'],
            'tips': ['조리법을 튀김에서 굽기나 찜으로 변경', '지방 함량이 낮은 단백질 선택']
        },
        'calories_kcal': {
            'foods_to_reduce': ['고칼로리 간식', '단 음료', '알코올'],
            'alternatives': ['과일', '물', '무칼로리 음료'],
            'tips': ['식사량 조절', '간식 대신 과일 선택', '규칙적인 운동']
        },
        'carbs_g': {
            'foods_to_reduce': ['흰밥', '빵', '과자', '단 음료'],
            'alternatives': ['현미', '통곡물', '채소'],
            'tips': ['단순 탄수화물을 복합 탄수화물로 교체', '섬유질이 풍부한 식품 선택']
        }
    }
    
    gender_info = "성인 남성" if gender == "male" else "성인 여성"
    
    recommendation_parts = []
    recommendation_parts.append("🔍 **AI 키가 설정되지 않아 통계 기반으로 감소 방법을 제공합니다**")
    recommendation_parts.append("")
    recommendation_parts.append(f"⚠️ **{gender_info} 기준 과다 섭취 영양소 감소 방법:**")
    recommendation_parts.append("")
    
    for nutrient, excess in excessive_nutrients.items():
        nutrient_name = get_nutrient_korean_name(nutrient)
        rdi_amount = rdi_info.get(nutrient, 0)
        
        if rdi_amount > 0:
            percentage_excess = round((excess / rdi_amount) * 100, 1)
            advice = reduction_advice.get(nutrient, {
                'foods_to_reduce': ['과도한 섭취 식품'],
                'alternatives': ['균형잡힌 대안 식품'],
                'tips': ['적정량 섭취 조절']
            })
            
            recommendation_parts.append(f"**{nutrient_name}** ({percentage_excess}% 초과)")
            recommendation_parts.append(f"• 줄여야 할 음식: {', '.join(advice['foods_to_reduce'][:3])}")
            recommendation_parts.append(f"• 대안 음식: {', '.join(advice['alternatives'][:3])}")
            recommendation_parts.append(f"• 실천 방법: {advice['tips'][0]}")
            recommendation_parts.append("")
    
    recommendation_parts.append("💡 **일반적인 조언:**")
    recommendation_parts.append("• 식품 영양성분표를 확인하는 습관을 기르세요")
    recommendation_parts.append("• 적당한 운동으로 신진대사를 활발하게 하세요")
    recommendation_parts.append("• 규칙적인 식사 시간을 유지하세요")
    
    return "\n".join(recommendation_parts)
