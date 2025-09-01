# ⚠️ 숫자는 프로젝트에 맞게 수정하세요. (KDRIs/식약처 고시 등)
# 기본값: 보편적인 라벨 기준값 + 보수적 캡

# 표시 순서 (테이블/그래프)
DISPLAY_ORDER = [
    "total_volume_g",
    "total_volume_ml",
    "calories_kcal",
    "carbs_g",
    "sugars_g",
    "fat_g",
    "sat_fat_g",
    "trans_fat_g",
    "cholesterol_mg",
    "sodium_mg",
    "protein_g",
]

# 여성(성인, 2000kcal 가정)
RDI_FEMALE = {
    "calories_kcal": 2000.0,
    "carbs_g": 300.0,      # 필요 시 324g 등으로 조정
    "sugars_g": 50.0,      # 총당류 상한 가이드(프로젝트 용도)
    "fat_g": 54.0,         # 라벨 기준값 계열
    "sat_fat_g": 15.0,
    "trans_fat_g": 2.0,    # 0에 가까울수록 좋음. 2g을 100%로 캡핑
    "cholesterol_mg": 300.0,
    "sodium_mg": 2000.0,
    "protein_g": 55.0,
}

# 남성(성인, 2500~2600kcal 가정)
RDI_MALE = {
    "calories_kcal": 2500.0,
    "carbs_g": 375.0,      # 2500 kcal 기준 60% 가정 시 예시
    "sugars_g": 60.0,
    "fat_g": 70.0,
    "sat_fat_g": 20.0,
    "trans_fat_g": 2.0,
    "cholesterol_mg": 300.0,
    "sodium_mg": 2000.0,
    "protein_g": 65.0,
}

