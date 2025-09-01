import re
from typing import Dict, Any, List
from rdi import DISPLAY_ORDER

# OCR 결과에서 문자열을 회수하고, 한국어 영양 키워드를 찾아 값/단위를 파싱합니다.
# 반환 키는 rdi.py 의 키와 동일하게 맞춥니다.
# - calories_kcal
# - sodium_mg
# - carbs_g
# - sugars_g
# - fat_g
# - sat_fat_g
# - trans_fat_g
# - cholesterol_mg
# - protein_g

NUM = r"([0-9]+(?:[\.,][0-9]+)?)"
UNIT_NUM = r"([0-9]+(?:[\.,][0-9]+)?)\s*(mg|g|kcal)"

# 키워드 우선순위/동의어
KEY_PATTERNS = [
    ("calories_kcal", [r"열량", r"칼로리", r"kcal"], rf"{NUM}\s*k?cal"),
    ("sodium_mg", [r"나트륨"], rf"{NUM}\s*mg"),
    ("carbs_g", [r"탄수화물"], rf"{NUM}\s*g"),
    ("sugars_g", [r"당류", r"당"], rf"{NUM}\s*g"),
    ("fat_g", [r"지방"], rf"{NUM}\s*g"),
    ("sat_fat_g", [r"포화지방"], rf"{NUM}\s*g"),
    ("trans_fat_g", [r"트랜스지방"], rf"{NUM}\s*g"),
    ("cholesterol_mg", [r"콜레스테롤"], rf"{NUM}\s*mg"),
    ("protein_g", [r"단백질"], rf"{NUM}\s*g"),
    ("total_volume_g", [r"내용량", r"총량", r"중량"], rf"{NUM}\s*g"),
    ("total_volume_ml", [r"내용량", r"총량", r"중량"], rf"{NUM}\s*ml"),
]


def _collect_texts(ocr_json: Dict[str, Any]) -> List[str]:
    texts = []
    try:
        images = ocr_json.get("images", [])
        for img in images:
            for f in img.get("fields", []):
                t = f.get("inferText") or f.get("inferTextRaw")
                if t:
                    texts.append(str(t))
    except Exception:
        pass
    return texts


def _to_float(s: str) -> float:
    return float(s.replace(",", "."))


def parse_ocr_payload(ocr_json: Dict[str, Any]) -> Dict[str, float]:
    texts = _collect_texts(ocr_json)
    joined = "\n".join(texts)

    out: Dict[str, float] = {}
    for key, aliases, num_pat in KEY_PATTERNS:
        # 1) 줄 수준에서 "키워드 ... 값 단위" 형식 매칭
        found = False
        for line in texts:
            if any(re.search(a, line) for a in aliases):
                m = re.search(num_pat, line, flags=re.IGNORECASE)
                if m:
                    out[key] = _to_float(m.group(1))
                    found = True
                    break
        if found:
            continue

        # 2) 전체 텍스트에서 "키워드" 근처의 숫자 단위 매칭 (OCR이 줄바꿈을 이상하게 준 경우)
        idx = None
        for a in aliases:
            m = re.search(a, joined)
            if m:
                idx = m.end()
                break
        if idx is not None:
            window = joined[idx : idx + 80]  # 키워드 이후 80자 안에서 숫자/단위 탐지
            m2 = re.search(num_pat, window, flags=re.IGNORECASE)
            if m2:
                out[key] = _to_float(m2.group(1))

    # 읽기 실패한 항목들을 0으로 채우기
    return fill_missing_fields(out)


def fill_missing_fields(fields: Dict[str, float]) -> Dict[str, float]:
    """읽기 실패한 영양성분 항목들을 None으로 표시합니다 (OCR 데이터 없음)."""
    filled = dict(fields)
    for key in DISPLAY_ORDER:
        if key not in filled:
            filled[key] = None  # OCR 데이터 없음을 의미
    
    return filled


def merge_totals(base: Dict[str, float], add: Dict[str, float]) -> Dict[str, float]:
    out = dict(base)
    for k, v in add.items():
        if v is None:
            continue
        out[k] = (out.get(k, 0.0) or 0.0) + float(v)
    return out


def normalize_units(d: Dict[str, float]) -> Dict[str, float]:
    # 이미 키명에 단위가 반영되어 있어 별도 변환 없음. 필요 시 단위 변환 추가.
    return d


def calculate_full_package_nutrition(fields: Dict[str, float]) -> Dict[str, float]:
    """총 내용량 기준으로 전체 패키지의 영양성분을 계산합니다."""
    # 총 내용량 확인 (g 또는 ml)
    total_volume = fields.get("total_volume_g") or fields.get("total_volume_ml")
    
    if not total_volume:
        # 내용량 정보가 없으면 기존 값 그대로 반환 (100g 기준으로 가정)
        return fields
    
    # 100g 기준 -> 전체 패키지 기준으로 환산
    multiplier = total_volume / 100.0
    
    full_package = {}
    for key, value in fields.items():
        if key.startswith("total_volume"):
            full_package[key] = value  # 내용량은 그대로 유지
        elif value is not None:
            full_package[key] = value * multiplier
    
    return full_package