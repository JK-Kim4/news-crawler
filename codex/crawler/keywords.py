import re

# AI-related keywords used for filtering and tagging.
# Note: some words (agent, vector, inference, attention, diffusion, prompt) have common
# non-AI meanings — false positives are an accepted trade-off at this stage.
KEYWORDS = [
    "LLM",
    "RAG",
    "transformer",
    "inference",
    "embedding",
    "fine-tuning",   # canonical form; matches both "fine-tuning" and "fine_tuning"
    "agent",
    "multimodal",
    "vector",
    "diffusion",
    "RLHF",
    "prompt",
    "tokenizer",
    "attention",
    "GPT",
    "BERT",
    "LoRA",
    "quantization",
]

# fine-tuning / fine_tuning are the same concept — match both with one pattern,
# store as the canonical tag "fine-tuning".
_KEYWORD_PATTERNS = {
    kw: re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
    for kw in KEYWORDS
}
_KEYWORD_PATTERNS["fine-tuning"] = re.compile(r"\bfine[-_]tuning\b", re.IGNORECASE)


def extract_keywords(text: str) -> list[str]:
    """
    Extract AI-related keywords from text.

    Returns:
        Deduplicated list of matched keywords (canonical casing from KEYWORDS).
    """
    return [kw for kw in KEYWORDS if _KEYWORD_PATTERNS[kw].search(text)]


def is_ai_related(title: str, content: str) -> bool:
    """
    Determine if content is AI-related based on keywords.

    Args:
        title: Article title
        content: Article content

    Returns:
        True if at least one AI keyword is found in title + content, False otherwise
    """
    combined_text = title + " " + content
    keywords = extract_keywords(combined_text)
    return len(keywords) > 0
