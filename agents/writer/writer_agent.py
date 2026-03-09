"""Writer Agent — tercer agente del pipeline editorial.

Transforma analyst_briefs en artículos editoriales con la voz de la marca.
Lee voice.md + formatos al arrancar, genera contenido en español,
guarda posts como pending_review, y solicita traducción al inglés.

Pipeline por brief:
1. Seleccionar formato según contenido del brief
2. Generar artículo con Claude Sonnet (voice + formato + brief)
3. Guardar post en tabla posts (status: pending_review)
4. Solicitar traducción via translate-post
5. Actualizar brief → status: processed
"""

import logging
from datetime import datetime, timezone

from agents.writer.editorial_loader import load_voice, load_formats
from agents.writer.format_selector import select_format
from agents.writer.content_generator import generate_article
from agents.writer.supabase_io import fetch_pending_briefs, save_post, update_brief_status
from agents.writer.translator import translate_post

logger = logging.getLogger(__name__)


class WriterAgent:
    """Genera artículos editoriales a partir de briefs del Analyst."""

    def __init__(self, batch_size: int = 10, editorial_dir: str = "editorial"):
        self.batch_size = batch_size

        # Carga editorial — fatal si falla
        self.voice = load_voice(editorial_dir)
        self.formats = load_formats(editorial_dir)

        logger.info(
            f"WriterAgent inicializado — "
            f"formatos: {list(self.formats.keys())}, "
            f"batch_size: {batch_size}"
        )

    def run(self) -> list[dict]:
        """Ejecuta un ciclo de escritura."""
        start = datetime.now(timezone.utc)
        logger.info(f"[{start.isoformat()}] Writer iniciando ciclo")

        briefs = fetch_pending_briefs(limit=self.batch_size)
        if not briefs:
            logger.info("No hay briefs pendientes. Ciclo terminado.")
            return []

        logger.info(f"Briefs a procesar: {len(briefs)}")

        posts = []
        errors = 0
        for brief in briefs:
            try:
                post = self._process_brief(brief)
                posts.append(post)
            except Exception as e:
                errors += 1
                brief_id = brief.get("id", "?")
                logger.error(f"Error procesando brief {brief_id}: {e}")
                continue  # no actualizar brief — reintento en próximo ciclo

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.info(
            f"Writer ciclo completado en {elapsed:.1f}s — "
            f"procesados: {len(posts)}, errores: {errors}"
        )
        return posts

    def _process_brief(self, brief: dict) -> dict:
        """Procesa un solo brief: formato → artículo → post → traducción."""
        brief_id = brief["id"]
        title = brief.get("title", "?")
        logger.info(f"Procesando brief: {title} ({brief_id})")

        # 1. Seleccionar formato
        format_name = select_format(brief, list(self.formats.keys()))
        format_template = self.formats[format_name]

        # 2. Generar artículo
        article = generate_article(brief, self.voice, format_template, format_name)

        # 3. Construir post
        post_data = {
            "title": article["title"],
            "content": article["content"],
            "excerpt": article["excerpt"],
            "tags": brief.get("tags", brief.get("topics", [])),
            "content_format": format_name,
            "status": "pending_review",
            "created_by": "writer-agent",
            "original_language": "es",
            "analyst_brief_id": brief_id,
        }

        # 4. Guardar post
        saved_post = save_post(post_data)

        # 5. Traducción (best-effort)
        post_id = saved_post.get("id") if isinstance(saved_post, dict) else None
        if post_id:
            translated = translate_post(post_id)
            if not translated:
                logger.warning(f"Traducción falló para post {post_id}, pero el post existe")

        # 6. Actualizar brief → processed
        update_brief_status(brief_id, "processed")

        logger.info(
            f"Brief procesado: {title} → formato: {format_name}, "
            f"post: {post_id or 'sin id'}"
        )
        return saved_post
