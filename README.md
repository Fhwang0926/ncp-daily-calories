# 영양정보 OCR 시각화 (Flask + Naver Cloud OCR)

여러 장의 영양 성분표 이미지를 업로드 → Clova OCR → 항목/수치 파싱 → 남/녀 기준 1일 권장섭취량 대비를 **사람 실루엣 물 채우기 그래프**로 보여줍니다.

## 1) 준비
1. 네이버클라우드 Clova OCR 콘솔에서 **엔드포인트 URL**과 **X-OCR-SECRET** 발급.
2. `.env` 파일을 생성하고 값 채우기 (또는 환경변수로 주입).
3. 필요하면 `rdi.py`의 RDI 값을 정책에 맞게 수정.

## 2) 실행
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)  # Windows는 set 대신 사용
python app.py
# http://localhost:8000 접속
```

### Docker

```bash
docker build -t nutrition-ocr .
docker run --rm -p 8000:8000 --env-file .env nutrition-ocr
```

## 3) 사용법

* 메인 화면에서 영양성분표 이미지를 **여러 개** 선택해 업로드합니다.
* 각 이미지의 OCR 결과를 파싱하여 **총합**을 계산합니다.
* 남/녀 기준의 **전체 평균 비율**을 사람 실루엣에 채워서 보여주고, 각 항목별 막대바도 표기합니다.

## 4) 커스터마이징

* `parser.py`의 키워드/정규식으로 항목 매칭을 보강하세요(예: 영어 라벨, 순서/레이아웃 변화 등).
* `rdi.py`에서 RDI와 표시 순서를 바꿀 수 있습니다.
* 실루엣 그래프(`static/style.css`, `static/person.js`)는 CSS Mask 기반으로 구현되어 있으며, SVG 마스크를 교체하면 모양/스타일을 쉽게 바꿀 수 있습니다.

## 5) 주의

* OCR 정확도는 원본 해상도, 조명, 왜곡 등에 따라 달라집니다. 업로드 전 **크롭/회전/보정**을 권장합니다.
* 특정 제품은 1회 제공량/100g 기준이 섞여 있을 수 있으니, 파싱 로직에서 기준을 통일하거나 제품별 배수를 반영하도록 확장하세요.

## 폴더 구조

```
nutrition-ocr-app/
├─ app.py
├─ ocr_client.py
├─ parser.py
├─ rdi.py
├─ requirements.txt
├─ README.md
├─ env.example
├─ Dockerfile
├─ templates/
│  ├─ base.html
│  └─ index.html
└─ static/
   ├─ style.css
   └─ person.js
```

## 환경변수 설정

`env.example` 파일을 참고하여 `.env` 파일을 생성하세요:

```
# Flask
FLASK_SECRET=change-me
PORT=8000

# Naver Cloud Clova OCR
NCP_OCR_ENDPOINT=https://naveropenapi.apigw.ntruss.com/vision-ocr/v1/general
NCP_OCR_SECRET=YOUR_OCR_SECRET
# 게이트웨이 키를 쓰는 계정일 경우 (선택)
# NCP_API_KEY_ID=YOUR_API_KEY_ID
# NCP_API_KEY=YOUR_API_KEY
```

## 기능

- **다중 이미지 업로드**: 여러 장의 영양성분표를 한 번에 업로드 가능
- **OCR 텍스트 추출**: 네이버클라우드 Clova OCR을 사용하여 이미지에서 텍스트 추출
- **영양성분 파싱**: 한국어 영양성분 키워드를 인식하여 수치 추출
- **시각화**: 사람 실루엣에 물이 차오르는 형태로 권장섭취량 대비 비율 표시
- **남녀별 기준**: 남성/여성 각각의 권장섭취량 기준으로 비교
- **반응형 UI**: 모던하고 직관적인 웹 인터페이스