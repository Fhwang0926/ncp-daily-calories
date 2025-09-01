import os
import base64
import json
import requests
from io import BytesIO
from PIL import Image
import numpy as np

# 네이버클라우드 Clova OCR (General) 예시 클라이언트
# 실제 엔드포인트/버전은 콘솔에서 발급받은 URL/Secret에 맞게 변경하세요.
# - ENDPOINT 예: https://naveropenapi.apigw.ntruss.com/vision-ocr/v1/general
# - Headers: X-OCR-SECRET (필수), X-NCP-APIGW-API-KEY-ID / -KEY (게이트웨이 설정 시)

ENDPOINT = os.environ.get("NCP_OCR_ENDPOINT")
SECRET = os.environ.get("NCP_OCR_SECRET")
API_KEY_ID = os.environ.get("NCP_API_KEY_ID", "")
API_KEY = os.environ.get("NCP_API_KEY", "")

# PaddleOCR 인스턴스 (필요시 생성)
_paddle_ocr = None


def get_paddle_ocr():
    """PaddleOCR 인스턴스를 가져오거나 생성합니다"""
    global _paddle_ocr
    if _paddle_ocr is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr = PaddleOCR(use_angle_cls=True, lang='korean')
        except ImportError:
            raise RuntimeError("PaddleOCR이 설치되지 않았습니다. 'pip install paddleocr' 실행하세요.")
    return _paddle_ocr


def paddle_ocr_process(image_bytes: bytes, filename: str = "image.jpg"):
    """PaddleOCR를 사용해서 이미지에서 텍스트를 추출합니다"""
    try:
        # 이미지 바이트를 numpy 배열로 변환
        image = Image.open(BytesIO(image_bytes))
        image_array = np.array(image)
        
        # PaddleOCR 실행
        ocr = get_paddle_ocr()
        result = ocr.ocr(image_array, cls=True)
        
        # 네이버 OCR 형식으로 변환
        fields = []
        if result and result[0]:
            for detection in result[0]:
                if detection and len(detection) >= 2:
                    bbox, (text, confidence) = detection
                    if confidence > 0.5:  # 신뢰도 임계값
                        fields.append({
                            "inferText": text,
                            "inferTextRaw": text,
                            "confidence": confidence
                        })
        
        # 네이버 OCR API 응답 형식으로 변환
        return {
            "version": "V2",
            "requestId": "paddle-ocr",
            "timestamp": 0,
            "images": [{
                "uid": filename,
                "name": filename,
                "inferResult": "SUCCESS",
                "message": "SUCCESS",
                "fields": fields
            }]
        }
        
    except Exception as e:
        raise RuntimeError(f"PaddleOCR 처리 중 오류: {e}")


def ncp_ocr_process(image_bytes: bytes, filename: str = "image.jpg"):
    """네이버 클라우드 OCR를 사용해서 이미지에서 텍스트를 추출합니다"""
    payload = {
        "version": "V2",
        "requestId": "webapp",
        "timestamp": 0,
        "lang": "ko",
        "images": [
            {
                "name": filename,
                "format": filename.split(".")[-1].lower(),
                "data": base64.b64encode(image_bytes).decode("utf-8"),
            }
        ],
    }

    headers = {"Content-Type": "application/json", "X-OCR-SECRET": SECRET}
    if API_KEY_ID and API_KEY:
        headers["X-NCP-APIGW-API-KEY-ID"] = API_KEY_ID
        headers["X-NCP-APIGW-API-KEY"] = API_KEY

    resp = requests.post(ENDPOINT, headers=headers, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    return resp.json()


def ncp_ocr(image_bytes: bytes, filename: str = "image.jpg"):
    """OCR 처리 메인 함수 - 네이버 키가 있으면 네이버 OCR, 없으면 PaddleOCR 사용"""
    
    # 네이버 클라우드 OCR 설정 확인
    if ENDPOINT and SECRET:
        try:
            print(f"네이버 클라우드 OCR 사용: {filename}")
            return ncp_ocr_process(image_bytes, filename)
        except Exception as e:
            print(f"네이버 OCR 실패, PaddleOCR로 대체: {e}")
    else:
        print(f"네이버 OCR 설정 없음, PaddleOCR 사용: {filename}")
    
    # PaddleOCR 사용
    return paddle_ocr_process(image_bytes, filename)