# ============================================================
# llm.py
# Clean LLM Factory (OpenAI / Gemini / Groq via OpenAI API)
# ============================================================

# Monkeypatch langchain_google_genai to disable its slow, hardcoded tenacity retries
try:
    import langchain_google_genai.chat_models as _chat_models
    from tenacity import retry, stop_after_attempt, retry_if_exception_type
    import google.api_core.exceptions as _exceptions

    def _fast_retry_decorator():
        return retry(
            reraise=True,
            stop=stop_after_attempt(1),  # Try exactly ONCE (0 retries) so fallback triggers instantly
            retry=retry_if_exception_type(_exceptions.GoogleAPIError)
        )
    _chat_models._create_retry_decorator = _fast_retry_decorator
except Exception:
    pass

from langchain_openai import ChatOpenAI
from config.settings import settings


def get_llm():
    provider = settings.LLM_PROVIDER.lower()

    # ================= OPENAI =================
    if provider == "openai":
        return ChatOpenAI(
            model=settings.LLM_MODEL_OPENAI,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
        )

    # ================= GROQ (OpenAI Compatible) =================
    elif provider == "groq":
        return ChatOpenAI(
            model="llama-3.1-8b-instant",
            openai_api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            temperature=settings.LLM_TEMPERATURE,
        )

    # ================= GEMINI =================
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        keys = settings.GOOGLE_API_KEYS
        if not keys:
            raise ValueError("No GOOGLE_API_KEY found in environment.")

        primary_llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL_GEMINI,
            google_api_key=keys[0],
            temperature=settings.LLM_TEMPERATURE,
            max_retries=0,
        )

        if len(keys) > 1:
            fallbacks = [
                ChatGoogleGenerativeAI(
                    model=settings.LLM_MODEL_GEMINI,
                    google_api_key=key,
                    temperature=settings.LLM_TEMPERATURE,
                    max_retries=0,
                )
                for key in keys[1:]
            ]
            return primary_llm.with_fallbacks(fallbacks)
        else:
            return primary_llm

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{provider}'. "
            "Choose 'openai', 'gemini', or 'groq'."
        )
