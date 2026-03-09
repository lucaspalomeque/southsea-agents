"""Cliente LLM unificado con soporte para Anthropic y OpenRouter.

Uso:
    from core.llm_client import completion

    text = completion("anthropic/claude-haiku-4-5-20251001", messages, max_tokens=4096)
    text = completion("openrouter/google/gemini-2.0-flash", messages, max_tokens=2048)

El formato de messages es siempre: [{"role": "user", "content": "..."}]
"""

import logging

import anthropic
import httpx

from core.config import ANTHROPIC_API_KEY, OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _parse_provider(model: str) -> tuple[str, str]:
    """Extrae provider y model_id de un string 'provider/model-id'.

    Sin prefijo asume anthropic.
    Para openrouter el model_id puede contener '/' (ej: google/gemini-2.0-flash).
    """
    if "/" not in model:
        return "anthropic", model
    prefix = model.split("/", 1)[0]
    rest = model[len(prefix) + 1:]
    if prefix in ("anthropic", "openrouter"):
        return prefix, rest
    raise ValueError(f"Provider desconocido: '{prefix}'. Usá 'anthropic' o 'openrouter'.")


def _call_anthropic(model_id: str, messages: list[dict], max_tokens: int, system: str | None = None) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY no definida. Revisá tu .env")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    kwargs = {
        "model": model_id,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text


def _call_openrouter(model_id: str, messages: list[dict], max_tokens: int, system: str | None = None) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY no definida. Revisá tu .env")
    all_messages = messages
    if system:
        all_messages = [{"role": "system", "content": system}] + messages
    response = httpx.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model_id,
            "messages": all_messages,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def completion(model: str, messages: list[dict], max_tokens: int = 2048, system: str | None = None) -> str:
    """Llama a un modelo LLM y retorna el texto de respuesta.

    Args:
        model: String con formato 'provider/model-id'.
               Providers: 'anthropic', 'openrouter'. Sin prefijo asume anthropic.
        messages: Lista de mensajes [{"role": "user", "content": "..."}].
        max_tokens: Máximo de tokens en la respuesta.
        system: Prompt de sistema opcional.

    Returns:
        Texto de la respuesta del modelo.
    """
    provider, model_id = _parse_provider(model)
    logger.info(f"LLM call: provider={provider} model={model_id} max_tokens={max_tokens}")

    if provider == "anthropic":
        return _call_anthropic(model_id, messages, max_tokens, system=system)
    return _call_openrouter(model_id, messages, max_tokens, system=system)
