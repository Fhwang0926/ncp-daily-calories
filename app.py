import os
import io
import base64
import zipfile
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify, Response
from werkzeug.utils import secure_filename
import tempfile
import uuid
import json
from flask_socketio import SocketIO, emit
import time
from ocr_client import ncp_ocr
from parser import parse_ocr_payload, merge_totals, normalize_units, calculate_full_package_nutrition
from rdi import RDI_MALE, RDI_FEMALE, DISPLAY_ORDER
from llm_client import get_nutrition_recommendation, calculate_deficient_nutrients, calculate_excessive_nutrients, get_reduction_recommendation, get_nutrition_recommendation_streaming, get_reduction_recommendation_streaming, get_comprehensive_nutrition_analysis_streaming

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

# SocketIO 초기화
socketio = SocketIO(app, cors_allowed_origins="*")

# 업로드된 이미지 임시 저장 폴더
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'temp_uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# nl2br 필터 추가 (개행문자를 <br> 태그로 변환)
@app.template_filter('nl2br')
def nl2br_filter(text):
    """개행문자를 <br> 태그로 변환하는 필터"""
    if text is None:
        return ""
    return text.replace('\n', '<br>\n')


def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT





@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/reset", methods=["POST", "GET"])
def reset():
    """초기화 버튼 처리 (POST) 및 새로고침 리다이렉트 처리 (GET)"""
    # Flash 메시지와 세션 데이터 클리어
    session.clear()
    
    # Flask의 flash 메시지 큐도 명시적으로 클리어
    if '_flashes' in session:
        session.pop('_flashes', None)
    
    # 임시 업로드 파일들도 정리
    try:
        import glob
        temp_files = glob.glob(os.path.join(UPLOAD_FOLDER, '*'))
        for temp_file in temp_files:
            if os.path.isfile(temp_file):
                os.remove(temp_file)
    except Exception as e:
        print(f"임시 파일 정리 중 오류: {e}")
    
    # 초기화 완료 후 메인 페이지로 리다이렉트 (매개변수 추가)
    return redirect(url_for("index", from_reset="true"))


@app.route("/download-samples")
def download_samples():
    """기존 sample.zip 파일을 다운로드"""
    try:
        # 프로젝트 루트의 sample.zip 파일 경로
        sample_path = os.path.join(os.getcwd(), "sample.zip")
        
        if os.path.exists(sample_path):
            return send_file(
                sample_path,
                as_attachment=True,
                download_name="nutrition_samples.zip",
                mimetype="application/zip"
            )
        else:
            flash("샘플 파일을 찾을 수 없습니다.")
            return redirect(url_for("index"))
            
    except Exception as e:
        flash(f"샘플 파일 다운로드 중 오류: {e}")
        return redirect(url_for("index"))


@app.route("/uploaded_image/<filename>")
def uploaded_image(filename):
    """업로드된 이미지 파일을 제공"""
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, filename))
    except Exception as e:
        return "Image not found", 404


@app.route("/upload", methods=["POST"])
def upload():
    if "images" not in request.files:
        flash("이미지 파일을 선택하세요.")
        return redirect(url_for("index"))

    files = request.files.getlist("images")
    images_bytes = []
    unsupported_files = []
    
    # 웹소켓으로 업로드 시작 신호 전송
    try:
        socketio.emit('analysis_progress', {
            'step': 'upload',
            'progress': 0,
            'message': f'{len(files)}개 파일 업로드 시작...',
            'total_files': len(files)
        })
    except:
        pass
    
    for f in files:
        if f and f.filename:  # 빈 파일명 체크 추가
            if allowed(f.filename):
                # 고유한 파일명 생성
                unique_filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                
                # 파일 내용 읽기
                file_content = f.read()
                
                # 실제 파일 내용이 있는지 확인
                if len(file_content) > 0:
                    # 임시 파일 저장 (미리보기용)
                    with open(file_path, 'wb') as temp_file:
                        temp_file.write(file_content)
                    
                    images_bytes.append((secure_filename(f.filename), file_content, unique_filename))
                else:
                    unsupported_files.append(f.filename)
            else:
                unsupported_files.append(f.filename)
    
    # 지원하지 않는 파일이 있을 때만 flash 메시지 표시
    if unsupported_files and images_bytes:  # 성공한 파일이 있을 때만
        flash(f"일부 파일은 지원하지 않는 형식입니다: {', '.join(unsupported_files)}")
    elif unsupported_files and not images_bytes:  # 모든 파일이 실패한 경우
        flash("업로드된 파일 중 지원되는 형식이 없습니다. PNG, JPG, JPEG, WEBP 파일을 선택해주세요.")
        return redirect(url_for("index"))

    if not images_bytes:
        return redirect(url_for("index"))

    # 업로드 완료 신호
    try:
        socketio.emit('analysis_progress', {
            'step': 'upload',
            'progress': 100,
            'message': f'{len(images_bytes)}개 파일 업로드 완료'
        })
    except:
        pass

    # OCR 호출 & 파싱 (진행 상황과 함께)
    per_image_results = []
    total_files = len(images_bytes)
    
    # OCR 시작 신호
    try:
        socketio.emit('analysis_progress', {
            'step': 'ocr',
            'progress': 0,
            'message': 'OCR 분석 시작...',
            'total_files': total_files
        })
    except:
        pass
    
    for idx, (fname, content, unique_filename) in enumerate(images_bytes, 1):
        try:
            # 진행 상황 메시지 및 웹소켓 신호
            progress_msg = f"분석 중... ({idx}/{total_files}) {fname}"
            print(progress_msg)  # 서버 로그에 출력
            
            # 파일별 OCR 진행 상황 전송
            ocr_progress = int(((idx - 1) / total_files) * 100)
            try:
                socketio.emit('analysis_progress', {
                    'step': 'ocr',
                    'progress': ocr_progress,
                    'message': f'OCR 분석 중: {fname} ({idx}/{total_files})',
                    'current_file': idx,
                    'total_files': total_files
                })
            except:
                pass
            
            ocr_json = ncp_ocr(content, filename=fname)
            fields = parse_ocr_payload(ocr_json)
            # 전체 패키지 기준으로 계산 (총 내용량 고려)
            full_package_fields = calculate_full_package_nutrition(fields)
            
            # OCR 원시 텍스트 추출
            ocr_texts = []
            try:
                images = ocr_json.get("images", [])
                for img in images:
                    for f in img.get("fields", []):
                        text = f.get("inferText") or f.get("inferTextRaw")
                        if text:
                            ocr_texts.append(str(text))
            except Exception:
                pass
            
            per_image_results.append({
                "filename": fname, 
                "fields": fields,  # 원본 (100g 기준)
                "full_package": full_package_fields,  # 전체 패키지 기준
                "ocr_texts": ocr_texts,  # OCR 원시 텍스트
                "status": "success",
                "image_url": url_for('uploaded_image', filename=unique_filename)
            })
            
        except Exception as e:
            error_msg = f"OCR 중 오류({fname}): {e}"
            flash(error_msg)
            # 오류 발생 시 PASS 상태로 추가 (합계 계산에서 제외)
            per_image_results.append({
                "filename": fname,
                "fields": None,
                "full_package": None,
                "status": "pass",
                "error": str(e),
                "image_url": url_for('uploaded_image', filename=unique_filename)
            })

    if not per_image_results:
        return redirect(url_for("index"))

    # OCR 완료 신호
    try:
        socketio.emit('analysis_progress', {
            'step': 'ocr',
            'progress': 100,
            'message': f'{total_files}개 파일 OCR 완료'
        })
    except:
        pass

    # 영양정보 추출 시작 신호
    try:
        socketio.emit('analysis_progress', {
            'step': 'nutrition',
            'progress': 0,
            'message': '영양성분 계산 시작...'
        })
    except:
        pass

    # 1. 합계 계산 (전체 패키지 기준) - PASS 상태는 제외
    try:
        socketio.emit('analysis_progress', {
            'step': 'nutrition',
            'progress': 20,
            'message': '영양성분 합계 계산 중...'
        })
    except:
        pass
    
    totals = {}
    for r in per_image_results:
        if r["status"] == "success" and r["full_package"] is not None:
            totals = merge_totals(totals, r["full_package"])

    # 2. 단위 정규화
    try:
        socketio.emit('analysis_progress', {
            'step': 'nutrition',
            'progress': 40,
            'message': '영양성분 단위 정규화 중...'
        })
    except:
        pass
    
    totals = normalize_units(totals)

    # 3. 남/녀 기준 백분율 계산
    try:
        socketio.emit('analysis_progress', {
            'step': 'nutrition',
            'progress': 60,
            'message': '남성/여성 기준 백분율 계산 중...'
        })
    except:
        pass
    
    def pct_map(totals_dict, rdi):
        out = {}
        for k, v in totals_dict.items():
            if k in rdi and rdi[k] > 0 and v is not None:
                out[k] = round(min(100.0, 100.0 * v / rdi[k]), 1)
        return out

    male_pct = pct_map(totals, RDI_MALE)
    female_pct = pct_map(totals, RDI_FEMALE)

    # 4. 전체 달성률 계산
    try:
        socketio.emit('analysis_progress', {
            'step': 'nutrition',
            'progress': 80,
            'message': '전체 달성률 계산 중...'
        })
    except:
        pass
    
    # 전체 실루엣 채움 비율(가중 평균). 단순 평균으로 시작
    keys_for_overall = [k for k in DISPLAY_ORDER if k in totals and totals[k] is not None]
    def overall(pcts):
        vals = [pcts.get(k, 0.0) for k in keys_for_overall if pcts.get(k) is not None]
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    male_overall = overall(male_pct)
    female_overall = overall(female_pct)
    
    # 칼로리 기준 달성률 계산
    male_calorie_achievement = 0.0
    female_calorie_achievement = 0.0
    
    if totals.get("calories_kcal") and totals["calories_kcal"] > 0:
        male_calorie_achievement = round((totals["calories_kcal"] / RDI_MALE["calories_kcal"]) * 100, 1)
        female_calorie_achievement = round((totals["calories_kcal"] / RDI_FEMALE["calories_kcal"]) * 100, 1)

    # 5. 부족/과다 영양소 분석
    try:
        socketio.emit('analysis_progress', {
            'step': 'nutrition',
            'progress': 90,
            'message': '부족/과다 영양소 분석 중...'
        })
    except:
        pass
        
    # 부족한 영양소 계산
    male_deficient = calculate_deficient_nutrients(totals, RDI_MALE)
    female_deficient = calculate_deficient_nutrients(totals, RDI_FEMALE)
    
    # 과다 영양소 계산
    male_excessive = calculate_excessive_nutrients(totals, RDI_MALE)
    female_excessive = calculate_excessive_nutrients(totals, RDI_FEMALE)

    # 영양정보 추출 완료 신호
    try:
        socketio.emit('analysis_progress', {
            'step': 'nutrition',
            'progress': 100,
            'message': '영양정보 추출 완료'
        })
    except:
        pass

    # AI 추천 생성 시작 신호 (웹소켓)
    try:
        socketio.emit('analysis_progress', {
            'step': 'recommendation',
            'progress': 0,
            'message': 'AI 추천 생성 시작...'
        })
    except:
        pass  # 웹소켓 연결이 없는 경우 무시

    # 종합 영양 분석 및 추천 (남성 기준) - 1번의 LLM 호출로 모든 분석
    print(f"DEBUG: Starting comprehensive male analysis")
    try:
        socketio.emit('analysis_progress', {
            'step': 'recommendation',
            'progress': 25,
            'message': '👨 남성 기준 종합 분석 중...'
        })
    except:
        pass
    
    male_comprehensive = get_comprehensive_nutrition_analysis_streaming(
        totals=totals,
        male_pct=male_pct,
        female_pct=female_pct,
        deficient_nutrients=male_deficient,
        excessive_nutrients=male_excessive,
        rdi_info=RDI_MALE,
        gender="male",
        socketio=socketio,
        session_id=None
    )
    print(f"DEBUG: Male comprehensive result (first 200 chars): {male_comprehensive[:200] if male_comprehensive else 'None'}")
    print(f"DEBUG: Male comprehensive contains API key message: {'AI 추천 서비스를 이용하려면 API 키가 필요합니다' in (male_comprehensive or '')}")
    
    # 종합 영양 분석 및 추천 (여성 기준) - 1번의 LLM 호출로 모든 분석
    print(f"DEBUG: Starting comprehensive female analysis")
    try:
        socketio.emit('analysis_progress', {
            'step': 'recommendation',
            'progress': 75,
            'message': '👩 여성 기준 종합 분석 중...'
        })
    except:
        pass
    
    female_comprehensive = get_comprehensive_nutrition_analysis_streaming(
        totals=totals,
        male_pct=male_pct,
        female_pct=female_pct,
        deficient_nutrients=female_deficient,
        excessive_nutrients=female_excessive,
        rdi_info=RDI_FEMALE,
        gender="female",
        socketio=socketio,
        session_id=None
    )
    print(f"DEBUG: Female comprehensive result (first 200 chars): {female_comprehensive[:200] if female_comprehensive else 'None'}")
    print(f"DEBUG: Female comprehensive contains API key message: {'AI 추천 서비스를 이용하려면 API 키가 필요합니다' in (female_comprehensive or '')}")
    
    # 기존 변수들을 종합 분석 결과로 설정 (호환성 유지)
    male_recommendation = male_comprehensive
    female_recommendation = female_comprehensive  # 각각의 성별 맞춤 종합 분석
    
    # 과다 섭취 영양소 감소 방법 생성 (별도 LLM 호출)
    print(f"DEBUG: Starting reduction recommendations")
    
    # 남성 기준 과다 섭취 감소 방법
    if male_excessive:
        try:
            socketio.emit('analysis_progress', {
                'step': 'recommendation',
                'progress': 80,
                'message': '👨 남성 과다 영양소 감소 방법 생성 중...'
            })
        except:
            pass
        male_reduction = get_reduction_recommendation_streaming(
            excessive_nutrients=male_excessive,
            rdi_info=RDI_MALE,
            gender="male",
            socketio=socketio,
            session_id=None
        )
        print(f"DEBUG: Male reduction result (first 100 chars): {male_reduction[:100] if male_reduction else 'None'}")
    else:
        male_reduction = ""
    
    # 여성 기준 과다 섭취 감소 방법
    if female_excessive:
        try:
            socketio.emit('analysis_progress', {
                'step': 'recommendation', 
                'progress': 85,
                'message': '👩 여성 과다 영양소 감소 방법 생성 중...'
            })
        except:
            pass
        female_reduction = get_reduction_recommendation_streaming(
            excessive_nutrients=female_excessive,
            rdi_info=RDI_FEMALE,
            gender="female",
            socketio=socketio,
            session_id=None
        )
        print(f"DEBUG: Female reduction result (first 100 chars): {female_reduction[:100] if female_reduction else 'None'}")
    else:
        female_reduction = ""
    
    # AI 사용 여부 최종 분석 및 로그 출력
    male_is_ai = male_recommendation and 'AI 추천 서비스를 이용하려면 API 키가 필요합니다' not in male_recommendation
    female_is_ai = female_recommendation and 'AI 추천 서비스를 이용하려면 API 키가 필요합니다' not in female_recommendation
    male_reduction_is_ai = male_reduction and 'AI 추천 서비스를 이용하려면 API 키가 필요합니다' not in male_reduction
    female_reduction_is_ai = female_reduction and 'AI 추천 서비스를 이용하려면 API 키가 필요합니다' not in female_reduction
    
    print("\n" + "="*80)
    print("🎯 영양 분석 완료 - AI 사용 현황 요약")
    print("="*80)
    print(f"👨 남성 기준 추천: {'🤖 AI 생성' if male_is_ai else '📊 통계 기반'}")
    if male_is_ai:
        print(f"   ✅ HyperCLOVA X API 응답 성공 (길이: {len(male_recommendation)}자)")
    else:
        print(f"   ⚠️  통계 기반 추천 사용 (API 키 없음 또는 실패)")
    
    if male_excessive:
        print(f"   👨 과다 영양소 감소: {'🤖 AI 생성' if male_reduction_is_ai else '📊 통계 기반'}")
        if male_reduction_is_ai:
            print(f"     ✅ 감소 방법 AI 생성 성공 (길이: {len(male_reduction)}자)")
    
    print(f"👩 여성 기준 추천: {'🤖 AI 생성' if female_is_ai else '📊 통계 기반'}")
    if female_is_ai:
        print(f"   ✅ HyperCLOVA X API 응답 성공 (길이: {len(female_recommendation)}자)")
    else:
        print(f"   ⚠️  통계 기반 추천 사용 (API 키 없음 또는 실패)")
    
    if female_excessive:
        print(f"   👩 과다 영양소 감소: {'🤖 AI 생성' if female_reduction_is_ai else '📊 통계 기반'}")
        if female_reduction_is_ai:
            print(f"     ✅ 감소 방법 AI 생성 성공 (길이: {len(female_reduction)}자)")
    
    # 전체 AI 사용률 계산 (추천 + 감소 방법)
    total_functions = 2  # 기본 남성/여성 추천
    ai_success_count = sum([male_is_ai, female_is_ai])
    
    if male_excessive:
        total_functions += 1
        ai_success_count += male_reduction_is_ai
    if female_excessive:
        total_functions += 1
        ai_success_count += female_reduction_is_ai
    
    ai_usage_rate = (ai_success_count / total_functions) * 100 if total_functions > 0 else 0
    
    print(f"\n🎯 AI 활용률: {ai_success_count}/{total_functions} ({ai_usage_rate:.0f}%)")
    
    if ai_usage_rate == 100:
        print("🌟 모든 추천이 AI로 생성되었습니다!")
    elif ai_usage_rate >= 50:
        print("⚡ 일부 추천이 AI로 생성되었습니다.")
    else:
        print("📊 대부분 통계 기반으로 생성되었습니다.")
    
    print("="*80 + "\n")

    # AI 추천 완료 및 분석 완료 신호
    try:
        socketio.emit('analysis_progress', {
            'step': 'complete',
            'progress': 100,
            'message': '모든 분석이 완료되었습니다!'
        })
    except:
        pass

    return render_template(
        "index.html",
        results={
            "images": per_image_results,
            "totals": totals,
            "male_pct": male_pct,
            "female_pct": female_pct,
            "male_overall": male_overall,
            "female_overall": female_overall,
            "male_calorie_achievement": male_calorie_achievement,
            "female_calorie_achievement": female_calorie_achievement,
            "display_order": DISPLAY_ORDER,
            "male_deficient": male_deficient,
            "female_deficient": female_deficient,
            "male_recommendation": male_recommendation,
            "female_recommendation": female_recommendation,
            "male_excessive": male_excessive,
            "female_excessive": female_excessive,
            "male_reduction": male_reduction,
            "female_reduction": female_reduction,
        },
    )


# 웹소켓 이벤트 핸들러
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_analysis')
def handle_join_analysis(data):
    session_id = data.get('session_id', request.sid)
    print(f'Client {request.sid} joined analysis session {session_id}')

# @socketio.on('start_analysis')
# 이 핸들러는 비활성화됨 - 실제 upload() 함수에서 진행 상황을 전송함
# def handle_start_analysis(data):
#     """실시간 분석 시작 - 웹소켓을 통해 진행 상황 전송"""
#     pass


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))