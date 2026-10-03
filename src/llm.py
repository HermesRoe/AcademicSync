import os
from dotenv import load_dotenv

load_dotenv()


def provider() -> str:
    return os.getenv("LLM_PROVIDER", "openai").lower()


def get_llm(temperature: float = 0.0):
    if provider() == "ollama":                       # free, local
        from langchain_ollama import ChatOllama
        return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"), temperature=temperature,
                          base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=temperature)


def structured(model, schema):
    """Structured output: JSON-schema mode for Ollama, function calling for OpenAI."""
    method = "json_schema" if provider() == "ollama" else "function_calling"
    return model.with_structured_output(schema, method=method)
