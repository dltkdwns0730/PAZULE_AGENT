keyword_mapping = {
    "화사한": [
        "sunny and bright",
        "vivid and colorful",
        "lively and vibrant",
    ],
    "차분한": [
        "warm and cozy",
        "calm and peaceful",
        "relaxed and comfortable",
    ],
    "활기찬": [
        "amusing and entertaining",
        "happy and pleasant",
        "busy and energetic",
        "dynamic and active",
    ],
    "자연적인": [
        "natural and scenic",
        "fresh and green",
        "serene and organic",
        "earthy and pure",
    ],
    "옛스러운": [
        "rural and rustic",
        "vintage and classic",
        "nostalgic and traditional",
    ],
    "신비로운": [
        "mysterious and dreamy",
        "magical and surreal",
        "fantastical and mystical",
    ],
    "웅장한": [
        "majestic and grand",
        "imposing and magnificent",
    ],
}

kw_strong = ["활기찬", "차분한"]
kw_middle = ["옛스러운", "화사한", "자연적인"]
kw_weak = ["신비로운", "웅장한"]

rules = [
    {"group": kw_strong, "top_k": 5},
    {"group": kw_middle, "top_k": 7},
    {"group": kw_weak, "top_k": 9},
]

feedback_guide = {
    "화사한": {
        "desc": "밝고 생기 있는 색감이나 조명이 필요합니다. 햇살, 꽃, 색감이 풍부한 피사체를 담아보세요!",
        "keywords": {
            "sunny and bright": "햇살 가득하고 밝은",
            "vivid and colorful": "생생하고 다채로운",
            "lively and vibrant": "활기 있고 에너지 넘치는",
        },
    },
    "차분한": {
        "desc": "부드럽고 안정적인 분위기를 연출해보세요. 잔잔한 빛, 따뜻한 색감, 여유 있는 구도를 활용해보세요!",
        "keywords": {
            "warm and cozy": "따뜻하고 포근한",
            "calm and peaceful": "고요하고 평화로운",
            "relaxed and comfortable": "편안하고 느긋한",
        },
    },
    "활기찬": {
        "desc": "사람의 움직임이나 강한 색감, 역동적인 구도를 담아보세요. 활력이 느껴지는 순간이 중요합니다!",
        "keywords": {
            "amusing and entertaining": "즐겁고 유쾌한",
            "happy and pleasant": "행복하고 기분 좋은",
            "busy and energetic": "분주하고 에너지 넘치는",
            "dynamic and active": "역동적이고 활발한",
        },
    },
    "자연적인": {
        "desc": "자연광, 식물, 나무, 바다처럼 자연의 질감을 강조해보세요. 인공적인 요소를 최소화하면 좋아요!",
        "keywords": {
            "natural and scenic": "자연스럽고 경치 좋은",
            "fresh and green": "싱그럽고 푸른",
            "serene and organic": "잔잔하고 유기적인",
            "earthy and pure": "소박하고 순수한",
        },
    },
    "옛스러운": {
        "desc": "레트로한 색감, 오래된 건축물, 따뜻한 톤을 활용해 과거의 정취를 표현해보세요!",
        "keywords": {
            "rural and rustic": "시골스럽고 소박한",
            "vintage and classic": "빈티지하고 클래식한",
            "nostalgic and traditional": "향수 어리고 전통적인",
        },
    },
    "신비로운": {
        "desc": "빛과 그림자의 대비, 색감의 조화로 몽환적인 분위기를 만들어보세요. 실루엣이나 안개도 좋아요!",
        "keywords": {
            "mysterious and dreamy": "신비롭고 몽환적인",
            "magical and surreal": "마법 같고 초현실적인",
            "fantastical and mystical": "환상적이고 신비로운",
        },
    },
    "웅장한": {
        "desc": "넓은 공간감, 높은 건축물, 산이나 하늘처럼 거대한 스케일을 담아보세요!",
        "keywords": {
            "majestic and grand": "장엄하고 위대한",
            "imposing and magnificent": "위압적이고 웅장한",
        },
    },
}
