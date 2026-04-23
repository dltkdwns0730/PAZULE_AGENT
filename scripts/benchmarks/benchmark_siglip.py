import argparse
import sys
import os
import time
from typing import List, Dict

# Ensure project root is in path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.models.siglip2 import probe_with_siglip2
    from app.models.prompts import build_prompt_bundle
except ImportError as e:
    print(
        f"Error: Could not import project modules. Ensure you are running from the project root. ({e})"
    )
    sys.exit(1)

# Standard test set based on intro images
STANDARD_TESTS = [
    {"image": "intro5.jpg", "mission": "location", "answer": "활판공방 인쇄기"},
    {"image": "intro1.jpg", "mission": "location", "answer": "활돌이"},
    {"image": "intro2.jpg", "mission": "location", "answer": "마법천자문 손오공"},
    {"image": "intro3.jpg", "mission": "location", "answer": "나남출판사"},
    {"image": "intro5.jpg", "mission": "atmosphere", "answer": "옛스러운"},
]


def run_benchmark(tests: List[Dict[str, str]], base_path: str):
    print("| ID | Image | Type | Prompt (EN) | Score | Prediction | Latency |")
    print("|---|---|---|---|---|---|---|")

    for i, test in enumerate(tests, 1):
        img_filename = test["image"]
        img_path = os.path.join(base_path, img_filename)
        mission = test["mission"]
        answer = test["answer"]

        if not os.path.exists(img_path):
            print(
                f"| {i:02} | {img_filename} | {mission} | - | N/A | [ERR: FILE_NOT_FOUND] | N/A |"
            )
            continue

        # Build prompt bundle
        bundle = build_prompt_bundle(mission, answer)
        en_prompt = bundle.get("siglip2_candidates", ["-"])[0]

        # Measure latency
        start_time = time.time()
        result = probe_with_siglip2(mission, img_path, answer, bundle)
        latency = time.time() - start_time

        score = result.get("score", 0.0)
        label = result.get("label", "mismatch")

        print(
            f"| {i:02} | {img_filename} | {mission} | `{en_prompt}` | {score:.4f} | {label} | {latency:.2f}s |"
        )


def main():
    parser = argparse.ArgumentParser(
        description="PAZULE SigLIP2 Automated Benchmarking Tool"
    )
    parser.add_argument(
        "--image", help="Single image filename to test (relative to assets)"
    )
    parser.add_argument(
        "--mission",
        choices=["location", "atmosphere"],
        default="location",
        help="Mission type",
    )
    parser.add_argument("--answer", help="Answer keyword (KR)")
    parser.add_argument(
        "--assets", default="front/src/assets", help="Path to assets folder"
    )

    args = parser.parse_args()

    if args.image and args.answer:
        tests = [{"image": args.image, "mission": args.mission, "answer": args.answer}]
    else:
        print("No specific image/answer provided. Running standard test set...")
        tests = STANDARD_TESTS

    run_benchmark(tests, args.assets)


if __name__ == "__main__":
    main()
