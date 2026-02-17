# PAZULE

파주출판단지 보물찾기 AI 게임. 위치 기반 랜드마크 탐색 미션과 감성 촬영 미션을 수행하고, AI가 사진을 분석하여 미션 성공 여부를 판정한다.

---

## 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [기술 스택과 선택 근거](#기술-스택과-선택-근거)
3. [프로젝트 구조](#프로젝트-구조)
4. [미션 파이프라인](#미션-파이프라인)
5. [설치 및 실행](#설치-및-실행)
6. [API 명세](#api-명세)

---

## 프로젝트 개요

PAZULE는 두 종류의 미션을 제공한다.

- **미션1 (장소 찾기)**: 힌트를 보고 파주출판단지 내 특정 랜드마크를 찾아 촬영한다. AI가 사진 속 대상이 정답 랜드마크와 일치하는지 VQA(Visual Question Answering)로 검증한다.
- **미션2 (감성 촬영)**: 주어진 감성 키워드(화사한, 차분한, 활기찬 등)에 맞는 사진을 촬영한다. AI가 사진의 분위기를 분석하여 키워드와의 일치도를 판단한다.

미션 성공 시 쿠폰 코드가 발급된다.

---

## 기술 스택과 선택 근거

### Backend

| 기술 | 버전 | 선택 근거 |
|------|------|-----------|
| **Python** | 3.10+ | PyTorch, Transformers, LangChain 등 AI/ML 생태계의 사실상 표준 언어. 모델 로딩부터 API 서빙까지 단일 언어로 처리할 수 있어 의존성 경계가 줄어든다. |
| **Flask** | 2.3+ | 3개의 엔드포인트만 필요한 경량 API 서버. Django의 ORM/Admin/Auth 같은 기능이 불필요하고, FastAPI의 async 이점도 BLIP 추론이 동기 블로킹인 현 구조에서는 의미가 없다. Blueprint 기반 라우팅으로 충분한 모듈화가 가능하다. |
| **Flask-CORS** | 4.0+ | 프론트엔드(Vite dev server, localhost:5173)와 백엔드(Flask, localhost:8080)가 서로 다른 포트에서 동작하므로 Cross-Origin 요청 허용이 필수적이다. |

### AI/ML

| 기술 | 버전 | 선택 근거 |
|------|------|-----------|
| **PyTorch** | 2.0+ | BLIP 모델의 런타임 엔진. Transformers 라이브러리가 내부적으로 PyTorch 텐서 연산을 사용하며, CUDA 가속이 필요할 때 `torch.cuda.is_available()`로 자동 전환된다. |
| **Transformers** | 4.30+ | Hugging Face의 사전학습 모델 허브에서 BLIP VQA 모델(`Salesforce/blip-vqa-base`)을 2줄로 로드할 수 있다. 모델 다운로드, 토크나이저, 추론 파이프라인을 일관된 API로 제공하여 모델 교체 비용을 최소화한다. |
| **BLIP (Salesforce/blip-vqa-base)** | - | 미션1에서 랜드마크 검증, 미션2에서 시각 컨텍스트 추출 두 가지 역할을 모두 수행한다. 기존에 CLIP을 사용했으나, CLIP은 이미지-텍스트 유사도만 계산하므로 "이 조각상이 앉아있는가?"와 같은 구체적 질문에 답할 수 없다. BLIP VQA는 자연어 질문에 대해 자유형 답변을 생성하므로 랜드마크의 세부 특징(색상, 자세, 재질)을 개별적으로 검증할 수 있다. |
| **OpenAI GPT-4o-mini** | - | 두 가지 용도로 사용한다. (1) 미션1 실패 시 BLIP 오답 정보를 기반으로 추상적 힌트를 생성한다. 정답을 직접 노출하지 않으면서 부족한 특징을 은유적으로 전달해야 하므로 언어 생성 능력이 필요하다. (2) 미션2에서 BLIP이 추출한 시각 컨텍스트와 감성 키워드의 일치 여부를 판단한다. "밝고 따뜻한 색감"이 "화사한"에 해당하는지 같은 주관적 판단은 규칙 기반으로 처리하기 어렵다. 4o-mini를 선택한 이유는 비용 대비 충분한 판단 품질을 제공하기 때문이다. |
| **LangChain** | 0.1+ | ChatPromptTemplate으로 프롬프트를 구조화하고, `prompt \| llm` 체인 구문으로 LLM 호출을 선언적으로 작성한다. 프롬프트 변경 시 코드 수정 없이 템플릿만 교체할 수 있어 실험 반복이 빠르다. |
| **LangGraph** | 0.0.10+ | Council 아키텍처(Security -> Tech -> Design)를 StateGraph로 구현한다. 단순 함수 체이닝 대신 LangGraph를 사용하는 이유는 조건부 분기(Security 실패 시 즉시 종료)와 상태 공유(CouncilState TypedDict)를 그래프 레벨에서 선언적으로 표현할 수 있기 때문이다. 향후 에이전트 추가나 병렬 실행 확장 시 그래프 노드만 추가하면 된다. |

### 이미지 처리

| 기술 | 버전 | 선택 근거 |
|------|------|-----------|
| **Pillow** | 10.0+ | EXIF 메타데이터(촬영 시각, GPS 좌표) 추출과 이미지 포맷 변환에 사용한다. 파주출판단지 BBox 내부 촬영인지 검증하려면 GPS IFD 파싱이 필요한데, Pillow의 `getexif().get_ifd(0x8825)`로 DMS 좌표를 직접 읽을 수 있다. |
| **pillow-heif** | 0.13+ | iPhone 기본 촬영 포맷인 HEIC를 지원한다. 현장에서 참가자 대부분이 iPhone으로 촬영하므로 HEIC 처리는 필수적이다. `register_heif_opener()`를 한 번 호출하면 Pillow의 `Image.open()`이 HEIC 파일을 투명하게 처리한다. |

### Frontend

| 기술 | 버전 | 선택 근거 |
|------|------|-----------|
| **React** | 19+ | 인트로 -> 미션선택 -> 업로드 -> 결과 화면 전환과 쿠폰 히스토리 같은 클라이언트 상태 관리가 필요하다. useState/useEffect로 충분한 규모이므로 별도 상태 관리 라이브러리 없이 React만으로 구현했다. |
| **Vite** | 7+ | CRA(Create React App) 대비 개발 서버 기동이 수십 배 빠르고, HMR(Hot Module Replacement)이 즉각적이다. 프론트엔드 코드가 단일 App.jsx에 집중된 소규모 프로젝트에서 Webpack의 복잡한 설정은 불필요하다. |

### 환경 관리

| 기술 | 선택 근거 |
|------|-----------|
| **python-dotenv** | `.env` 파일에서 `OPENAI_API_KEY`를 로드한다. 환경변수를 코드와 분리하여 API 키가 저장소에 커밋되는 것을 방지한다. |

---

## 프로젝트 구조

```
PAZULE/
├── run.py                         # Flask 앱 팩토리 + 서버 기동
├── run_cli.py                     # 터미널 게임 루프
├── requirements.txt               # Python 의존성
├── .gitignore
├── app/
│   ├── api/
│   │   └── routes.py              # Flask Blueprint (3개 엔드포인트)
│   ├── core/
│   │   ├── config.py              # Settings (환경변수, 경로, 모델 ID)
│   │   └── keyword.py             # 감성 키워드 매핑 + 피드백 가이드
│   ├── council/
│   │   ├── state.py               # CouncilState TypedDict
│   │   ├── agents.py              # Security / Tech / Design 에이전트
│   │   └── graph.py               # LangGraph StateGraph 빌드
│   ├── metadata/
│   │   ├── metadata.py            # EXIF/GPS 추출 + BBox 검증
│   │   └── validator.py           # 통합 메타데이터 유효성 검증
│   ├── models/
│   │   ├── blip.py                # BLIP VQA (랜드마크 검증 + 시각 컨텍스트)
│   │   └── llm.py                 # LLMService (힌트 생성 + 감성 판단)
│   └── services/
│       ├── answer_service.py      # 일별 정답/힌트 관리 + 캐싱
│       ├── coupon_service.py      # 쿠폰 코드 생성/발급
│       └── mission_service.py     # run_mission1(), run_mission2()
├── data/
│   ├── answer.json                # 미션 정답 + 힌트
│   └── landmark_qa_labeled.json   # 랜드마크별 VQA 질문/답변 쌍
├── front/                         # React + Vite 프론트엔드
│   ├── src/
│   │   ├── App.jsx                # 전체 UI
│   │   ├── App.css                # 스타일
│   │   └── main.jsx               # 진입점
│   └── package.json
└── tests/
```

---

## 미션 파이프라인

### 공통 전처리

사용자가 이미지를 업로드하면 다음 순서로 전처리가 진행된다.

```
[사용자 이미지 업로드]
       |
       v
[1. 파일 형식 검증]
  - 허용 확장자: .jpg, .jpeg, .png, .heic, .heif
  - HEIC 파일은 pillow-heif로 투명 처리
       |
       v
[2. 메타데이터 검증] (metadata/validator.py -> metadata/metadata.py)
  - EXIF에서 촬영 날짜 추출 -> 오늘 촬영인지 확인
  - GPS IFD에서 위도/경도 추출 -> DMS를 십진수로 변환
  - 파주출판단지 BBox (37.704~37.719, 126.683~126.690) 내부인지 판정
  - 두 조건 모두 만족해야 통과
       |
       v
[3. 오늘의 정답 조회] (services/answer_service.py)
  - current_answer.json에 오늘 날짜로 캐싱된 정답이 있으면 반환
  - 없으면 answer.json에서 랜덤 선택 후 캐싱
       |
       v
[4. Council 파이프라인 진입] (council/graph.py)
```

### Council 파이프라인

LangGraph StateGraph로 구현된 3단계 에이전트 파이프라인이다.

```
[Security Agent] --안전--> [Tech Agent] --> [Design Agent] --> [최종 응답]
       |
       +--위험--> [즉시 종료]
```

**Stage 1: Security Agent** (`council/agents.py`)

입력의 안전성을 검증한다. 현재는 placeholder로 모든 요청을 통과시키며, 향후 Prompt Injection 탐지와 NSFW 이미지 필터링을 추가할 수 있도록 분리해두었다. `is_safe` 플래그가 False이면 Council 그래프가 즉시 종료된다.

**Stage 2: Tech Agent** (`council/agents.py` -> `services/mission_service.py`)

미션 타입에 따라 분기하여 핵심 AI 로직을 실행한다.

**Stage 3: Design Agent** (`council/agents.py`)

Tech Agent의 결과를 받아 사용자에게 보여줄 최종 응답을 디자인한다. 성공 시 GPT-4o-mini로 축하 메시지를 생성하고 UI 테마를 `confetti`로 설정한다. 실패 시 힌트와 격려 메시지를 `encouragement` 테마로 반환한다.

---

### 미션1: 장소 찾기 파이프라인

```
[Tech Agent]
     |
     v
[BLIP VQA 검증] (models/blip.py :: check_with_blip)
  - landmark_qa_labeled.json에서 정답 랜드마크의 질문 리스트 로드
  - 각 질문(예: "Is the statue purple?")에 대해 BLIP이 답변 생성
  - 모델 답변과 기대 답변(yes/no)을 비교하여 정답률 계산
  - 정답률 >= 75% 이면 성공
     |
     +--성공--> [쿠폰 발급] (services/coupon_service.py)
     |            - 8자리 랜덤 코드 생성
     |            - 미션 타입, 정답, 발급 시각 기록
     |
     +--실패--> [LLM 힌트 생성] (models/llm.py :: generate_blip_hint)
                  - BLIP이 틀린 질문 목록을 LLM에 전달
                  - "정답을 직접 언급하지 않고 추상적이고 시적인 힌트" 생성
                  - 예: 색상이 틀렸다면 "보랏빛 옷을 입은 누군가를 찾아보세요"
```

BLIP VQA 검증의 동작 원리를 상세히 설명하면 다음과 같다.

1. `landmark_qa_labeled.json`에는 랜드마크별로 20개의 긍정 질문(답: yes)과 20개의 부정 질문(답: no)이 정의되어 있다.
2. 긍정 질문은 해당 랜드마크의 고유 특징을 묻는다. 예를 들어 "마법천자문 손오공"에 대해 "Is the statue's clothing purple?", "Is the statue's hair red?" 등이다.
3. 부정 질문은 다른 랜드마크의 특징이나 무관한 대상을 묻는다. "Is the main object an airplane?", "Is the sculpture a cat?" 등이다.
4. 사용자가 정답 랜드마크를 촬영했다면 긍정 질문에 yes, 부정 질문에 no로 답할 확률이 높으므로 정답률이 75%를 넘는다.
5. 엉뚱한 대상을 촬영했다면 긍정 질문 대부분에서 틀리므로 정답률이 낮아진다.

---

### 미션2: 감성 촬영 파이프라인

```
[Tech Agent]
     |
     v
[BLIP 시각 컨텍스트 추출] (models/blip.py :: get_visual_context)
  - 6개의 탐색 질문으로 이미지의 전반적 분위기를 텍스트로 추출
    * "What is the atmosphere of this picture?"
    * "What is the dominant color?"
    * "Is this picture bright or dark?"
    * "How does this picture feel?"
    * "What objects are in the picture?"
    * "Is it natural or artificial?"
  - 각 질문-답변 쌍을 텍스트로 결합
     |
     v
[LLM 감성 판단] (models/llm.py :: verify_mood)
  - BLIP이 추출한 시각 컨텍스트와 목표 감성 키워드를 LLM에 전달
  - keyword.py의 feedback_guide에서 키워드 정의를 참조
    * 예: "화사한" = "밝고 생기 있는 색감이나 조명이 필요합니다"
  - LLM이 JSON 형태로 판단 결과 반환: {"success": true/false, "reason": "..."}
  - 엄격하지 않은 판단 기준 적용 (분위기가 어느 정도 느껴지면 성공)
     |
     +--성공--> [쿠폰 발급]
     |
     +--실패--> [reason 필드를 힌트로 반환]
```

미션2에서 CLIP 대신 BLIP + LLM 조합을 사용하는 이유는 다음과 같다.

- CLIP은 이미지와 텍스트 임베딩 간 코사인 유사도를 계산한다. "화사한"이라는 단일 키워드와의 유사도 점수만으로는 판단 근거를 사용자에게 설명할 수 없다.
- BLIP VQA로 "이 사진의 분위기는?", "주된 색상은?" 같은 구체적 질문을 던져 텍스트 컨텍스트를 추출하면, LLM이 그 컨텍스트를 읽고 "밝은 색감과 햇살이 느껴져 화사한 분위기와 일치합니다"처럼 판단 근거를 자연어로 제공할 수 있다.
- 실패 시에도 "어두운 톤이 많아 화사한 느낌이 부족합니다" 같은 구체적 피드백을 줄 수 있어 사용자 경험이 향상된다.

---

## 설치 및 실행

### 사전 요구사항

- Python 3.10 이상
- Node.js 18 이상 (프론트엔드)
- OpenAI API Key

### 백엔드

```bash
cd PAZULE

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
echo "OPENAI_API_KEY=sk-..." > .env

# 서버 실행
python run.py
```

서버가 `http://localhost:8080`에서 기동된다.

### CLI 모드

```bash
python run_cli.py
```

터미널에서 힌트를 확인하고 이미지 경로를 입력하여 플레이한다.

### 프론트엔드

```bash
cd front

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

`http://localhost:5173`에서 브라우저로 접속한다.

---

## API 명세

### GET /get-today-hint

오늘의 미션 힌트와 정답을 반환한다.

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `mission_type` | query string | `location` (미션1) 또는 `photo` (미션2). 기본값 `location` |

응답 예시:
```json
{"answer": "지혜의숲 조각상", "hint": "줌-인(ZOOM-IN)"}
```

### POST /api/preview

업로드된 이미지를 JPEG로 변환하여 반환한다. HEIC 파일의 브라우저 미리보기에 사용한다.

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `image` | form-data (file) | 이미지 파일 |

응답: `image/jpeg` 바이너리

### POST /api/mission

미션을 제출하고 AI 판정 결과를 반환한다.

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `image` | form-data (file) | 촬영한 이미지 |
| `mission_type` | form-data (string) | `location` 또는 `photo` |

성공 응답:
```json
{
  "success": true,
  "coupon": {
    "code": "A3X9K2M7",
    "description": "지혜의숲 조각상 장소 찾기 미션 완료 쿠폰",
    "mission_type": "mission1",
    "issued_at": "2026-02-17T14:30:00"
  }
}
```

실패 응답:
```json
{
  "success": false,
  "hint": "보랏빛 무늬가 새겨진 여행자를 찾아보세요.",
  "message": "장소를 다시 찾아보세요!"
}
```
