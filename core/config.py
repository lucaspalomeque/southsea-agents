import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Variable de entorno requerida '{name}' no está definida. "
            f"Revisá tu archivo .env"
        )
    return value


# Requeridas — el sistema no arranca sin estas
SUPABASE_URL: str = _require("SUPABASE_URL")
AGENTS_API_KEY: str = _require("AGENTS_API_KEY")

# Requeridas por agente — fallan al usarse, no al importar
ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY") or None
OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY") or None
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN") or None
_channels = os.getenv("TELEGRAM_CHANNEL_NAMES")
TELEGRAM_CHANNEL_NAMES: list[str] | None = _channels.split(",") if _channels else None

# Bot de notificación del pipeline (independiente del Publisher)
SOUTHSEA_BOT_TOKEN: str | None = os.getenv("SOUTHSEA_BOT_TOKEN") or None
SOUTHSEA_CHAT_ID: str | None = os.getenv("SOUTHSEA_CHAT_ID") or None
