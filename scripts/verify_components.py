"""PAZULE 파이프라인 컴포넌트 개별 검증 스크립트.

4가지 핵심 컴포넌트를 독립적으로 호출하여 PASS/FAIL을 리포트한다:
  1. GPS 메타데이터 검증
  2. VLM 모델 프로브 (Qwen / BLIP / SigLIP2)
  3. 앙상블 취합 + 판정
  4. LLM 힌트 생성 (오답 시나리오)

사용법:
  python scripts/verify_components.py
  python scripts/verify_components.py --image "C:\\path\\to\\photo.jpg"
  python scripts/verify_components.py --answer "한길책박물관" --mission-type location
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# ── 색상 유틸리티 ──────────────────────────────────────────────
PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"
SKIP = "⏭️  SKIP"

results: list[dict] = []


import threading
import sys

def _record(section: str, item: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    results.append({"section": section, "item": item, "passed": passed})
    print(f"\r    → {item}: {status}{f'  ({detail})' if detail else ''}")


def _record_skip(section: str, item: str, reason: str):
    results.append({"section": section, "item": item, "passed": None})
    print(f"\r    → {item}: {SKIP}  ({reason})")


class ProgressLogger:
    def __init__(self, msg: str):
        self.msg = msg
        self._stop_event = threading.Event()
        self._thread = None
        self.start_time = None

    def _animate(self):
        while not self._stop_event.is_set():
            elapsed = time.time() - self.start_time
            now = datetime.now().strftime("%H:%M:%S")
            sys.stdout.write(f"\r  [{now}] ⏳ {self.msg} (시간: {elapsed:.1f}s 진행중...)")
            sys.stdout.flush()
            self._stop_event.wait(0.5)
            
    def __enter__(self):
        self.start_time = time.time()
        now = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"  [{now}] ⏳ {self.msg} 시작됨...\n")
        sys.stdout.flush()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()


def _log_progress(msg: str):
    # Backward compatibility, but we will use the context manager where possible
    now = datetime.now().strftime("%H:%M:%S")
    print(f"  [{now}] ⏳ {msg}", flush=True)


def _section(num: int, total: int, title: str):
    print(f"\n[{num}/{total}] {title}")


# ── 1. GPS 메타데이터 검증 ─────────────────────────────────────

def verify_gps(image_path: str):
    """GPS 좌표 추출 및 BBox 범위 검증."""
    section = "GPS 메타데이터"
    _section(1, 4, "GPS 메타데이터 검증")

    from app.metadata.metadata import extract_gps_coordinates, is_in_bbox

    # 1-a: 이미지에서 GPS 추출 시도
    try:
        coords = extract_gps_coordinates(image_path)
        if coords:
            lat, lon = coords
            _record(section, "GPS 추출", True, f"lat={lat:.6f}, lon={lon:.6f}")
            inside = is_in_bbox(lat, lon)
            _record(section, "BBox 판정 (실제 좌표)", inside,
                    f"{'출판단지 내부' if inside else '출판단지 외부'}")
        else:
            _record(section, "GPS 추출", True, "GPS 데이터 없음 — None 반환 (정상)")
    except Exception as e:
        _record(section, "GPS 추출", False, str(e))

    # 1-b: BBox 로직 자체 검증 (하드코딩 좌표)
    try:
        # 파주출판단지 내부 좌표
        assert is_in_bbox(37.710, 126.685) is True
        _record(section, "BBox 검증 (내부 좌표)", True, "37.710, 126.685 → True")
    except AssertionError:
        _record(section, "BBox 검증 (내부 좌표)", False, "expected True")
    except Exception as e:
        _record(section, "BBox 검증 (내부 좌표)", False, str(e))

    try:
        # 범위 외 좌표
        assert is_in_bbox(0.0, 0.0) is False
        _record(section, "BBox 검증 (외부 좌표)", True, "0.0, 0.0 → False")
    except AssertionError:
        _record(section, "BBox 검증 (외부 좌표)", False, "expected False")
    except Exception as e:
        _record(section, "BBox 검증 (외부 좌표)", False, str(e))


# ── 2. VLM 모델 프로브 ────────────────────────────────────────

REQUIRED_VOTE_KEYS = {"model", "score", "label", "reason"}


def _validate_vote(vote: dict) -> tuple[bool, str]:
    """모델 투표 결과가 필수 키를 포함하는지 검증."""
    missing = REQUIRED_VOTE_KEYS - set(vote.keys())
    if missing:
        return False, f"missing keys: {missing}"
    if vote.get("label") == "fail":
        return False, f"label=fail, reason={vote.get('reason', 'N/A')}"
    score = vote.get("score", -1)
    if not isinstance(score, (int, float)) or score < 0:
        return False, f"invalid score: {score}"
    return True, f"score={score:.2f}, label={vote['label']}"


def verify_models(image_path: str, answer: str, mission_type: str):
    """Qwen, BLIP, SigLIP2 세 모델의 프로브 호출 검증."""
    section = "VLM 모델 프로브"
    _section(2, 4, "VLM 모델 프로브 검증")

    from app.models.prompts import build_prompt_bundle

    prompt_bundle = build_prompt_bundle(mission_type, answer)
    all_votes = []

    # 2-a: Qwen (OpenRouter API)
    try:
        from app.models.qwen_vl import probe_with_qwen

        with ProgressLogger("Qwen (OpenRouter API) 비전 검증") as p:
            vote = probe_with_qwen(mission_type, image_path, answer, prompt_bundle)
            elapsed = time.time() - p.start_time
            
        ok, detail = _validate_vote(vote)
        _record(section, f"Qwen (OpenRouter API, {elapsed:.1f}s)", ok, detail)
        all_votes.append(vote)
    except Exception as e:
        _record(section, "Qwen (OpenRouter API)", False, str(e))
        traceback.print_exc()

    # 2-b: BLIP (HuggingFace)
    try:
        from app.models.blip import probe_with_blip_location, probe_with_blip_atmosphere

        with ProgressLogger("BLIP VQA 모델 검증 (로컬 연산)") as p:
            if mission_type == "location":
                vote = probe_with_blip_location(image_path, answer, prompt_bundle)
            else:
                vote = probe_with_blip_atmosphere(image_path, answer, prompt_bundle)
            elapsed = time.time() - p.start_time
            
        ok, detail = _validate_vote(vote)
        _record(section, f"BLIP (HuggingFace VQA, {elapsed:.1f}s)", ok, detail)
        all_votes.append(vote)
    except Exception as e:
        _record(section, "BLIP (HuggingFace VQA)", False, str(e))
        traceback.print_exc()

    # 2-c: SigLIP2 (HuggingFace)
    try:
        from app.models.siglip2 import probe_with_siglip2

        with ProgressLogger("SigLIP2 로컬 모델 매칭 검증") as p:
            vote = probe_with_siglip2(mission_type, image_path, answer, prompt_bundle)
            elapsed = time.time() - p.start_time
            
        ok, detail = _validate_vote(vote)
        _record(section, f"SigLIP2 (Image-Text, {elapsed:.1f}s)", ok, detail)
        all_votes.append(vote)
    except Exception as e:
        _record(section, "SigLIP2 (Image-Text)", False, str(e))
        traceback.print_exc()

    return all_votes


# ── 3. 앙상블 취합 + 판정 ──────────────────────────────────────

def verify_aggregation(model_votes: list[dict], mission_type: str):
    """aggregator + judge 노드 검증."""
    section = "앙상블 취합 + 판정"
    _section(3, 4, "앙상블 취합 + 판정")

    if not model_votes:
        _record_skip(section, "Aggregator", "모델 투표 결과 없음 — 이전 단계 실패")
        _record_skip(section, "Judge", "Aggregator 미실행")
        return

    from app.council.nodes import aggregator, judge

    # 3-a: Aggregator
    try:
        agg_state = {
            "request_context": {"mission_type": mission_type},
            "artifacts": {"model_votes": model_votes},
        }
        agg_out = aggregator(agg_state)
        ensemble = agg_out.get("artifacts", {}).get("ensemble_result", {})
        merged = ensemble.get("merged_score", -1)
        threshold = ensemble.get("threshold", -1)
        conflict = ensemble.get("conflict", None)

        ok = merged >= 0 and threshold >= 0 and conflict is not None
        detail = f"merged_score={merged:.4f}, threshold={threshold}, conflict={conflict}"
        _record(section, "Aggregator", ok, detail)
    except Exception as e:
        _record(section, "Aggregator", False, str(e))
        traceback.print_exc()
        return

    # 3-b: Judge
    try:
        judge_state = {
            "artifacts": {
                "gate_result": {"passed": True, "risk_flags": []},
                "ensemble_result": ensemble,
                "model_votes": model_votes,
            },
            "errors": [],
            "control_flags": {},
        }
        judge_out = judge(judge_state)
        judgment = judge_out.get("artifacts", {}).get("judgment", {})
        success = judgment.get("success")
        reason = judgment.get("reason", "N/A")

        ok = isinstance(success, bool) and reason != "N/A"
        _record(section, "Judge", ok, f"success={success}, reason={reason}")
    except Exception as e:
        _record(section, "Judge", False, str(e))
        traceback.print_exc()


# ── 4. LLM 힌트 생성 ──────────────────────────────────────────

def verify_llm_hint(answer: str):
    """오답 시나리오에서 LLM 힌트 생성 API 호출 검증."""
    section = "LLM 힌트 생성"
    _section(4, 4, "LLM 힌트 생성 (오답 시나리오)")

    # 4-a: 힌트 생성
    try:
        from app.models.llm import llm_service

        mock_failed_questions = [
            {
                "question": "Is there a large sign in the image?",
                "model_answer": "no",
                "expected_answer": "yes",
            },
            {
                "question": "What color is the building?",
                "model_answer": "white",
                "expected_answer": "brown",
            },
        ]

        with ProgressLogger("Gemini API 힌트 생성 요청") as p:
            hint = llm_service.generate_blip_hint_from_questions(answer, mock_failed_questions)
            elapsed = time.time() - p.start_time

        ok = isinstance(hint, str) and len(hint) > 0
        detail = f"응답 길이: {len(hint)}자, 소요: {elapsed:.1f}s"
        if ok and len(hint) > 60:
            detail += f'\n    힌트 미리보기: "{hint[:60]}..."'
        elif ok:
            detail += f'\n    힌트: "{hint}"'
        _record(section, "Gemini API 힌트 생성", ok, detail)
    except Exception as e:
        _record(section, "Gemini API 힌트 생성", False, str(e))
        traceback.print_exc()


# ── 메인 실행 ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PAZULE 파이프라인 컴포넌트 검증")
    parser.add_argument(
        "--image",
        default=os.path.join(PROJECT_ROOT, "docs", "assets", "test_sample.png"),
        help="검증에 사용할 이미지 경로",
    )
    parser.add_argument("--answer", default=None, help="미션 정답 키워드 (기본값: current_answer.json)")
    parser.add_argument(
        "--mission-type",
        default="location",
        choices=["location", "atmosphere"],
        help="미션 유형 (기본값: location)",
    )
    args = parser.parse_args()

    # 정답 결정
    answer = args.answer
    if not answer:
        try:
            from app.services.answer_service import get_today_answers
            a1, a2, _, _ = get_today_answers()
            answer = a1 if args.mission_type == "location" else a2
        except Exception:
            answer = "한길책박물관" if args.mission_type == "location" else "웅장한"

    # 프롬프트 레지스트리 + 모델 레지스트리 초기화
    from app.core.config import settings
    try:
        from app.prompts.registry import PromptRegistry
        PromptRegistry.get_instance().load_all(settings.PROMPT_TEMPLATES_DIR)
    except Exception:
        pass  # 프롬프트 없어도 기본값으로 동작

    from app.models.model_registry import register_default_models
    register_default_models()

    # 헤더
    sep = "=" * 60
    print(f"\n{sep}")
    print("  PAZULE Component Verification")
    print(sep)
    print(f"  이미지:      {args.image}")
    print(f"  미션 타입:   {args.mission_type}")
    print(f"  정답 키워드: {answer}")
    print(sep)

    if not os.path.exists(args.image):
        # 기본 이미지가 없으면 자동 생성
        print(f"\n  {WARN} 이미지 없음 — 테스트용 이미지를 자동 생성합니다...")
        try:
            from PIL import Image as PILImage
            os.makedirs(os.path.dirname(args.image), exist_ok=True)
            test_img = PILImage.new("RGB", (640, 480), (100, 150, 200))
            test_img.save(args.image)
            print(f"  → 생성 완료: {args.image}")
        except Exception as e:
            print(f"\n{FAIL} 테스트 이미지 자동 생성 실패: {e}")
            print(f"  --image 옵션으로 직접 이미지 경로를 지정해주세요.")
            sys.exit(1)

    # 실행
    t_total = time.time()
    verify_gps(args.image)
    model_votes = verify_models(args.image, answer, args.mission_type)
    verify_aggregation(model_votes, args.mission_type)
    verify_llm_hint(answer)
    elapsed_total = time.time() - t_total

    # 요약
    passed = sum(1 for r in results if r["passed"] is True)
    failed = sum(1 for r in results if r["passed"] is False)
    skipped = sum(1 for r in results if r["passed"] is None)
    total = len(results)

    print(f"\n{sep}")
    print(f"  결과: {passed}/{total} PASS", end="")
    if failed:
        print(f"  |  {failed} FAIL", end="")
    if skipped:
        print(f"  |  {skipped} SKIP", end="")
    print(f"  |  총 소요: {elapsed_total:.1f}s")
    print(sep)

    if failed:
        print(f"\n{FAIL} 실패 항목:")
        for r in results:
            if r["passed"] is False:
                print(f"  - [{r['section']}] {r['item']}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
