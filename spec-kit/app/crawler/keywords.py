"""AI keyword extraction for article filtering and tagging."""

AI_KEYWORDS = [
    "인공지능", "AI", "머신러닝", "딥러닝", "GPT", "LLM", "자연어처리", "NLP",
    "컴퓨터비전", "강화학습", "신경망", "트랜스포머", "생성형", "ChatGPT",
    "Claude", "Gemini", "LLaMA", "BERT", "diffusion", "stable diffusion",
    "대규모 언어 모델", "파인튜닝", "프롬프트", "RAG", "벡터 DB",
    "machine learning", "deep learning", "neural network", "transformer",
    "reinforcement learning", "computer vision", "natural language",
    "generative AI", "foundation model", "multimodal", "AGI",
    "artificial intelligence", "embedding", "tokenizer", "attention",
]

AI_KEYWORDS_LOWER = [k.lower() for k in AI_KEYWORDS]


def extract_keywords(text: str) -> list[str]:
    """Extract matching AI keywords from text. Returns list of matched keywords."""
    if not text:
        return []
    text_lower = text.lower()
    matched = []
    for i, keyword in enumerate(AI_KEYWORDS_LOWER):
        if keyword in text_lower:
            matched.append(AI_KEYWORDS[i])
    return matched
