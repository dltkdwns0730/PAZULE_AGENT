"""Prompt bundles for model-specific probes."""

from __future__ import annotations

from typing import Dict


def build_prompt_bundle(mission_type: str, answer: str) -> Dict[str, Dict[str, str]]:
    """Caller: ?? ?? ???? ???
    Purpose: `build_prompt_bundle` ?? ??? ????
    Returns: ?? ?? ?? ??
    Deps: ?? ??? ??
    Args: mission_type: ???? ???? ??; answer: ???? ???? ??
    Note: ?? ?? ?? ???? ???"""
    mission = "atmosphere" if mission_type == "photo" else mission_type
    if mission not in {"location", "atmosphere"}:
        mission = "location"

    if mission == "location":
        return {
            "blip": {
                "system": "랜드마크의 세부 속성(객체, 자세, 재질, 색상)을 확인한다.",
                "user": f"정답 랜드마크는 '{answer}' 이다. 이미지에서 해당 장소가 맞는지 검증하라.",
            },
            "clip": {
                "system": "이미지-텍스트 유사도 관점으로 장소 후보를 비교한다.",
                "user": f"'{answer}'와 이미지가 의미적으로 얼마나 유사한지 점수화하라.",
            },
            "qwen": {
                "system": "비전 판정관으로서 증거 기반 yes/no를 반환한다.",
                "user": (
                    f"목표 장소: {answer}. "
                    "입력된 시각 설명을 보고 JSON {label,score,confidence,reason}으로 답하라."
                ),
            },
            "siglip2": {
                "system": "대조학습 임베딩 관점에서 장소 텍스트와 이미지 정합성을 본다.",
                "user": f"'{answer}' 텍스트와 이미지 임베딩 정합 점수를 계산한다.",
            },
        }

    return {
        "blip": {
            "system": "이미지 분위기를 설명 가능한 텍스트로 분해한다.",
            "user": f"목표 감성은 '{answer}' 이다. 이미지 분위기를 설명하고 부합 여부를 판단하라.",
        },
        "clip": {
            "system": "감성 키워드와 이미지 의미 유사도를 계산한다.",
            "user": f"'{answer}' 감성과 이미지의 의미 유사도를 점수로 산출하라.",
        },
        "qwen": {
            "system": "분위기 판정관으로 근거와 함께 정답 부합 여부를 판단한다.",
            "user": (
                f"목표 감성: {answer}. "
                "입력 설명을 읽고 JSON {label,score,confidence,reason}으로 답하라."
            ),
        },
        "siglip2": {
            "system": "이미지-텍스트 임베딩 정렬로 감성 부합도를 계산한다.",
            "user": f"'{answer}' 감성 텍스트와 이미지 유사도를 계산한다.",
        },
    }
