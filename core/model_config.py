"""Configuración centralizada de modelos por tarea.

Para cambiar el modelo o provider de un agente, solo tocá este dict.
"""

# Formato: "provider/model-id"
# Providers: anthropic/, openrouter/
# Ejemplos OpenRouter: openrouter/google/gemini-2.0-flash,
#   openrouter/deepseek/deepseek-chat, openrouter/mistralai/mistral-large
# Sin prefijo = anthropic (backward compatible)
MODELS = {
    "scout.classifier": "openrouter/deepseek/deepseek-v3.2",
    "analyst.researcher": "anthropic/claude-sonnet-4-20250514",
    "analyst.brief_builder": "anthropic/claude-sonnet-4-20250514",
    "writer.content_generator": "anthropic/claude-sonnet-4-20250514",
    "editor.evaluator": "openrouter/deepseek/deepseek-v3.2",
}
