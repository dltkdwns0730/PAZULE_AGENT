# SigLIP2 Benchmark Report Template

> **Category**: Benchmark · **Version**: 2.0 (Standardized)
> **Metadata**: [Model ID] · [Hardware] · [Date]

## 1. Environment Metadata

| Attribute | Value |
|---|---|
| **Model ID** | `google/siglip2-base-patch16-224` |
| **Backend** | `app.models.siglip2` |
| **Execution Device** | CPU / CUDA |
| **Torch Version** | 2.x.x |
| **Transformers Version** | 4.x.x |

## 2. Test Objectives

- [ ] Verify baseline accuracy for Location missions.
- [ ] Verify baseline accuracy for Atmosphere missions.
- [ ] Audit the impact of English Descriptive Prompts vs. KR Keywords.

---

## 3. Results Table

| ID | Image | Type | Prompt (EN/KR) | Score | Prediction | Status |
|---|---|---|---|---|---|---|
| 01 | `intro5.jpg` | Location | a photo of ... | 0.0000 | Match/Mismatch | PENDING |
| 02 | `intro5.jpg` | Atmosphere | a photo with ... | 0.0000 | Match/Mismatch | PENDING |

---

## 4. Key Metrics Summary

- **Average Match Score**: 0.0000
- **Average Mismatch Score**: 0.0000
- **Average Inference Latency**: 0.00s per image
- **Decision Threshold (Current)**: 0.70

## 5. Observations & Insights

- (To be filled after running `scripts/benchmark_siglip.py`)

---

## 6. How to Reproduce

```bash
uv run python scripts/benchmark_siglip.py --image intro5.jpg --mission location --answer "활판공방 인쇄기"
```
