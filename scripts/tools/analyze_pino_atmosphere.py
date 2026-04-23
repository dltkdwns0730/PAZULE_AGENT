import os
import json
from app.models.model_registry import register_default_models, ModelRegistry
from app.models.prompts import build_prompt_bundle

def analyze_pino():
    register_default_models()
    registry = ModelRegistry.get_instance()
    siglip2 = registry.get("siglip2")
    blip = registry.get("blip")
    
    pino_dir = "data/assets/피노키오"
    if not os.path.exists(pino_dir):
        pino_dir = "data/assets/pino" # 혹시 이름이 바뀌었을 경우 대비
    
    images = [f for f in os.listdir(pino_dir) if f.lower().endswith(('.jpg', '.png'))][:3] # 샘플 3장
    
    results = {}
    
    # 1. 일반적인 묘사 (Captioning)
    # 2. 잠재적 후보군 테스트
    candidates = {
        "장난스러운": "playful, whimsical, and toy-like atmosphere",
        "동화 같은": "fairytale-like, storybook style, and magical mood",
        "소박한": "rustic, simple, and wooden textured atmosphere",
        "인공적인": "artificial, plastic-like, and manufactured scene"
    }

    for img_name in images:
        img_path = os.path.join(pino_dir, img_name)
        print(f"\n--- Analyzing: {img_name} ---")
        
        # BLIP Caption
        caption = blip.probe("location", img_path, "", {})["reason"]
        print(f"BLIP Caption: {caption}")
        
        # Candidate Scores
        scores = {}
        for name, desc in candidates.items():
            # 임시 번들 생성
            bundle = {
                "siglip2_candidates": [f"a photo with {desc}", "a photo with a different atmosphere"]
            }
            res = siglip2.probe("atmosphere", img_path, name, bundle)
            scores[name] = res["score"]
            print(f"  {name}: {res['score']:.4f}")
            
    return

if __name__ == "__main__":
    analyze_pino()
