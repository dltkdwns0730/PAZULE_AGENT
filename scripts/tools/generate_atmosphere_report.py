import json
import os
from urllib.parse import quote

GT_PATH = "data/atmosphere_ground_truth_siglip2.json"
ASSETS_DIR = "data/assets"
REPORT_PATH = "atmosphere_verification_report_siglip2.html"

def generate_html_report():
    if not os.path.exists(GT_PATH):
        print("Ground truth data not found.")
        return

    with open(GT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Atmosphere Label Verification</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 40px; color: #333; }
            h1 { text-align: center; color: #1a73e8; margin-bottom: 40px; }
            .container { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; max-width: 1400px; margin: 0 auto; }
            .card { background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); overflow: hidden; transition: transform 0.2s; }
            .card:hover { transform: translateY(-5px); }
            .img-container { width: 100%; height: 240px; overflow: hidden; background: #e8eaed; position: relative; }
            .card img { width: 100%; height: 100%; object-fit: contain; }
            .info { padding: 20px; }
            .filename { font-size: 0.75em; color: #70757a; word-break: break-all; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            .labels { margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 6px; }
            .label-tag { background: #e8f0fe; color: #1967d2; padding: 4px 10px; border-radius: 20px; font-size: 0.85em; font-weight: 500; border: 1px solid #d2e3fc; }
            .score-list { font-size: 0.85em; list-style: none; padding: 0; margin: 0; }
            .score-item { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #f8f9fa; }
            .score-item:last-child { border-bottom: none; }
            .high-score { font-weight: bold; color: #d93025; background: #fce8e6; border-radius: 4px; padding-left: 4px; padding-right: 4px; }
            .score-value { font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>PAZULE Atmosphere Verification</h1>
        <div class="container">
    """

    for rel_path, info in sorted(data.items()):
        # URL 인코딩 적용 (한글 경로 문제 해결)
        encoded_path = quote(rel_path.replace("\\", "/"))
        img_src = f"data/assets/{encoded_path}"
        
        labels_html = "".join([f'<span class="label-tag">{label}</span>' for label in info['labels']])
        
        scores_html = ""
        sorted_scores = sorted(info['scores'].items(), key=lambda x: x[1], reverse=True)
        for label, score in sorted_scores:
            is_high = score >= 0.3
            score_class = "high-score" if is_high else ""
            scores_html += f'<li class="score-item {score_class}"><span>{label}</span> <span class="score-value">{score:.4f}</span></li>'

        html_content += f"""
            <div class="card">
                <div class="img-container">
                    <img src="{img_src}" alt="{rel_path}" loading="lazy">
                </div>
                <div class="info">
                    <div class="filename">{rel_path}</div>
                    <div class="labels">{labels_html}</div>
                    <ul class="score-list">
                        {scores_html}
                    </ul>
                </div>
            </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Report generated: {os.path.abspath(REPORT_PATH)}")

    html_content += """
        </div>
    </body>
    </html>
    """

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Report generated: {os.path.abspath(REPORT_PATH)}")

if __name__ == "__main__":
    generate_html_report()
