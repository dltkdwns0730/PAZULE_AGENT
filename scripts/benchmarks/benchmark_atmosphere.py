
import os
import json
import logging
from datetime import datetime
from PIL import Image
from app.core.config import settings
from app.models.model_registry import register_default_models, ModelRegistry
from app.models.prompts import build_prompt_bundle

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AtmosphereBenchmark")

def run_benchmark():
    # 1. 모델 등록
    register_default_models()
    registry = ModelRegistry.get_instance()
    
    # 2. 테스트 대상 에셋 경로
    assets_base_dir = r"C:\Users\irubw\geminiProject\projects\active\PAZULE\data\assets"
    
    # 3. 테스트할 분위기 키워드 (answer.json 기반)
    # 실제 에셋 폴더명과 매칭하기 위해 매핑 필요할 수 있음
    # 여기서는 폴더명을 'answer'로 간주하거나, 수동 매핑
    test_cases = [
        {"folder": "나남출판사", "answer": "자연적인"},
        {"folder": "지혜의 숲", "answer": "웅장한"},
        {"folder": "지혜의 숲", "answer": "차분한"},
        {"folder": "로드킬 부엉이", "answer": "옛스러운"},
        {"folder": "활판 공방", "answer": "옛스러운"},
    ]
    
    # 4. 모델 목록 (SigLIP2, BLIP 위주)
    models_to_test = ["siglip2", "blip"]
    
    results = []
    
    for case in test_cases:
        folder_path = os.path.join(assets_base_dir, case["folder"])
        if not os.path.exists(folder_path):
            logger.warning(f"Folder not found: {folder_path}")
            continue
            
        # 폴더 내 첫 번째 이미지 사용
        images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            continue
            
        image_path = os.path.join(folder_path, images[0])
        answer = case["answer"]
        
        logger.info(f"Testing Folder: {case['folder']} | Image: {images[0]} | Target: {answer}")
        
        case_result = {
            "folder": case["folder"],
            "image": images[0],
            "target": answer,
            "scores": {}
        }
        
        prompt_bundle = build_prompt_bundle("atmosphere", answer)
        
        for model_name in models_to_test:
            try:
                probe = registry.get(model_name)
                # SigLIP2는 무거우므로 각 루프에서 메모리 관리 주의 (여기서는 순차 실행)
                res = probe.probe("atmosphere", image_path, answer, prompt_bundle)
                case_result["scores"][model_name] = res["score"]
                logger.info(f"  -> {model_name}: {res['score']:.4f}")
            except Exception as e:
                logger.error(f"  -> {model_name} Error: {e}")
                case_result["scores"][model_name] = 0.0
                
        results.append(case_result)
        
    # 결과 요약 저장
    report_path = "atmosphere_benchmark_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nBenchmark completed. Report saved to {report_path}")

if __name__ == "__main__":
    run_benchmark()
