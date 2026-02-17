import io
import os
import tempfile

from flask import Blueprint, jsonify, request, send_file
from PIL import Image
from pillow_heif import register_heif_opener

from app.metadata.validator import validate_metadata
from app.services.answer_service import get_today_answers

api = Blueprint("api", __name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


@api.route("/get-today-hint", methods=["GET"])
def get_today_hint():
    """오늘의 힌트와 정답을 반환한다.

    Query Params:
        mission_type: "location"(미션1) 또는 "photo"(미션2). 기본값 "location".
    """
    mission_type = request.args.get("mission_type", "location")

    try:
        a1, a2, h1, h2 = get_today_answers()
        if mission_type == "photo":
            return jsonify({"answer": a2, "hint": h2})
        return jsonify({"answer": a1, "hint": h1})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/api/preview", methods=["POST"])
def api_preview():
    """업로드된 HEIC 이미지를 JPG로 변환하여 반환한다.

    브라우저 호환을 위해 pillow-heif로 HEIC를 처리한 뒤 JPEG으로 변환.
    """
    if "image" not in request.files:
        return jsonify({"error": "이미지 파일이 없습니다"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "파일이 선택되지 않았습니다"}), 400

    register_heif_opener()

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[1]
    ) as tmp_file:
        file.save(tmp_file.name)
        temp_path = tmp_file.name

    try:
        img = Image.open(temp_path).convert("RGB")
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=90)
        output.seek(0)
        return send_file(output, mimetype="image/jpeg", download_name="preview.jpg")
    except Exception as e:
        print(f"미리보기 오류: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@api.route("/api/mission", methods=["POST"])
def api_mission():
    """미션 제출을 검증하고 Council을 통해 실행한다.

    1. 파일 형식 및 메타데이터(날짜/위치) 검증
    2. 오늘의 정답 조회
    3. LLM Council (Security -> Tech -> Design) 호출
    4. 최종 응답 반환
    """
    if "image" not in request.files:
        return jsonify({"error": "이미지 파일이 없습니다"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "파일이 선택되지 않았습니다"}), 400

    mission_type = request.form.get("mission_type", "location")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "지원하지 않는 파일 형식입니다"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        file.save(tmp_file.name)
        temp_path = tmp_file.name

    try:
        # 1. 메타데이터 검증
        if not validate_metadata(temp_path):
            return jsonify({"error": "메타데이터 검증 실패 (날짜/위치 불일치)"}), 400

        # 2. 오늘의 정답 조회
        a1, a2, h1, h2 = get_today_answers()
        answer = a2 if mission_type == "photo" else a1

        # 3. Council을 통해 미션 실행
        from app.council.graph import council_app

        initial_state = {
            "request_type": "mission",
            "user_input": {
                "mission_type": mission_type,
                "image_path": temp_path,
                "answer": answer,
            },
            "is_safe": True,
            "messages": [],
        }

        output = council_app.invoke(initial_state)
        final_res = output.get("final_response")

        return jsonify(
            final_res.get("data") if final_res else {"error": "Council 실행 실패"}
        )
    except Exception as e:
        print(f"미션 실행 오류: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
