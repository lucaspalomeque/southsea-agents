"""Pytest fixtures para tests del Analyst Agent.

Setea variables de entorno dummy antes de que core.config se importe,
para que los tests no dependan de un .env real.
"""

import os
import sys

# Setear env vars ANTES de que cualquier modulo las lea
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co/functions/v1/agent-ingest")
os.environ.setdefault("AGENTS_API_KEY", "sk-test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")
