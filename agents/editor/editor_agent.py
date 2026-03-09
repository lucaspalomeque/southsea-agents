"""Editor Agent — cuarto agente del pipeline editorial.

Evalúa borradores del Writer en 4 dimensiones editoriales.
Solo dos acciones posibles: aprobar o devolver. Nunca descarta.

Pipeline por post:
1. Verificar revision_count (>= 2 → auto-aprobar con nota)
2. Cargar brief asociado del Analyst
3. Evaluar con Claude Haiku (4 dimensiones + regla de veto)
4. Guardar review en editor_reviews
5. Actualizar post → pending_review (aprobado) o needs_revision (devuelto)
"""

import logging
from datetime import datetime, timezone

from agents.editor.editorial_loader import load_voice, load_formats
from agents.editor.evaluator import evaluate
from agents.editor.supabase_io import (
    fetch_pending_posts,
    fetch_brief,
    save_review,
    approve_post,
    return_post,
)

logger = logging.getLogger(__name__)

MAX_REVISIONS = 2
HUMAN_NOTE_AUTO_APPROVE = "Post aprobado tras 2+ revisiones. Requiere atención editorial humana."


class EditorAgent:
    """Evalúa posts del Writer y decide si aprobar o devolver."""

    def __init__(self, batch_size: int = 10, editorial_dir: str = "editorial"):
        self.batch_size = batch_size

        # Carga editorial — fatal si falla
        self.voice = load_voice(editorial_dir)
        self.formats = load_formats(editorial_dir)

        logger.info(
            f"EditorAgent inicializado — "
            f"formatos: {list(self.formats.keys())}, "
            f"batch_size: {batch_size}"
        )

    def run(self) -> list[dict]:
        """Ejecuta un ciclo de edición."""
        start = datetime.now(timezone.utc)
        logger.info(f"[{start.isoformat()}] Editor iniciando ciclo")

        posts = fetch_pending_posts(limit=self.batch_size)
        if not posts:
            logger.info("No hay posts pendientes de edición. Ciclo terminado.")
            return []

        logger.info(f"Posts a evaluar: {len(posts)}")

        reviews = []
        errors = 0
        for post in posts:
            try:
                review = self._process_post(post)
                reviews.append(review)
            except Exception as e:
                errors += 1
                post_id = post.get("id", "?")
                logger.error(f"Error evaluando post {post_id}: {e}")
                continue

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.info(
            f"Editor ciclo completado en {elapsed:.1f}s — "
            f"evaluados: {len(reviews)}, errores: {errors}"
        )
        return reviews

    def _process_post(self, post: dict) -> dict:
        """Procesa un solo post: evalúa y toma decisión."""
        post_id = post["id"]
        title = post.get("title", "?")
        revision_count = post.get("revision_count", 0)

        logger.info(f"Procesando post: {title} ({post_id}), revision_count={revision_count}")

        # Regla de revision_count: auto-aprobar si >= MAX_REVISIONS
        if revision_count >= MAX_REVISIONS:
            logger.info(f"Post {post_id} con {revision_count} revisiones → auto-aprobado")
            return self._auto_approve(post)

        # Cargar brief asociado (best-effort)
        brief_id = post.get("analyst_brief_id")
        brief = None
        if brief_id:
            try:
                brief = fetch_brief(brief_id)
            except Exception as e:
                logger.warning(f"No se pudo cargar brief {brief_id}: {e}")

        # Determinar formato y template
        content_format = post.get("content_format", "analysis")
        format_template = self.formats.get(content_format, "")
        if not format_template:
            logger.warning(f"Formato '{content_format}' no encontrado, usando evaluación sin template")

        # Evaluar con Haiku
        evaluation = evaluate(post, brief, self.voice, format_template)

        # Construir review (esquema real de editor_reviews)
        review_data = {
            "post_id": post_id,
            "decision": evaluation["decision"],
            "voice_alignment": evaluation["scores"]["voice_alignment"],
            "factual_rigor": evaluation["scores"]["factual_rigor"],
            "format_compliance": evaluation["scores"]["format_compliance"],
            "thematic_alignment": evaluation["scores"]["thematic_alignment"],
            "overall_score": evaluation["average_score"],
            "summary": evaluation["feedback"],
            "revision_notes": None,
        }

        # Guardar review (best-effort — tabla puede no existir aún)
        try:
            save_review(review_data)
        except Exception as e:
            logger.warning(f"No se pudo guardar review para {post_id}: {e}")

        # Actualizar post según decisión (best-effort)
        try:
            if evaluation["decision"] == "approved":
                approve_post(post_id)
                logger.info(f"Post aprobado: {title}")
            else:
                return_post(post_id, revision_count)
                logger.info(f"Post devuelto: {title} — feedback: {evaluation['feedback'][:100]}")
        except Exception as e:
            logger.warning(f"No se pudo actualizar post {post_id}: {e}")

        return review_data

    def _auto_approve(self, post: dict) -> dict:
        """Aprueba automáticamente un post con nota para el humano."""
        post_id = post["id"]

        review_data = {
            "post_id": post_id,
            "decision": "approved",
            "summary": "Auto-aprobado por exceder máximo de revisiones.",
            "revision_notes": HUMAN_NOTE_AUTO_APPROVE,
        }

        saved_review = save_review(review_data)
        approve_post(post_id)

        logger.info(f"Post {post_id} auto-aprobado con nota para humano")
        return saved_review
