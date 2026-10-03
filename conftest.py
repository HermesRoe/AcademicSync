import pytest
from src import llm


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    """Tests never call the real LLM; nodes fall back to deterministic text."""
    def boom(*a, **k):
        raise RuntimeError("LLM disabled in tests")
    monkeypatch.setattr(llm, "get_llm", boom)
