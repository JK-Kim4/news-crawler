from crawler.keywords import extract_keywords, is_ai_related


def test_extract_keywords_case_insensitive():
    text = "Using LLM and RAG for retrieval"
    keywords = extract_keywords(text)
    assert "LLM" in keywords
    assert "RAG" in keywords


def test_extract_keywords_no_match():
    text = "Python web framework tutorial"
    keywords = extract_keywords(text)
    assert keywords == []


def test_is_ai_related_true():
    assert is_ai_related("title", "content with transformer and embedding") is True


def test_is_ai_related_false():
    assert is_ai_related("Docker tutorial", "how to use containers") is False


def test_extract_keywords_deduplication():
    text = "LLM LLM LLM transformer"
    keywords = extract_keywords(text)
    assert keywords.count("LLM") == 1


def test_extract_keywords_word_boundary():
    text = "prompt engineering is useful"
    keywords = extract_keywords(text)
    assert "prompt" in keywords
