"""ARQ worker for asynchronous receipt processing.

The worker picks up queued jobs, runs the VLM extraction pipeline,
validates the results, and writes everything back to the database.

Usage (start the worker)::

    arq app.extraction.worker.WorkerSettings

Configuration is read from the app's central config module.
"""

from __future__ import annotations

import logging
from typing import Any

from arq.connections import RedisSettings  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


async def process_receipt(ctx: dict[str, Any], receipt_id: int) -> None:
    """Process a single receipt: extract fields, validate, store results.

    This function is enqueued by the API endpoint after a photo upload.
    It runs inside the ARQ worker process.

    Args:
        ctx: ARQ worker context (contains ``redis`` connection, etc.).
        receipt_id: primary-key of the receipt row to process.
    """
    # Late imports so the worker module can be imported without a full
    # app context (ARQ only needs the WorkerSettings at import time).
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SASession

    from app.extraction.validator import validate_receipt_fields
    from app.extraction.vlm_extractor import get_extractor

    # Import models and config from the main app package.
    # These are expected to exist once the rest of the backend is built.
    try:
        from app.config import settings  # type: ignore[import-untyped]
        from app.models import Receipt  # type: ignore[import-untyped]
    except ImportError as exc:
        logger.error(
            "Cannot import app.config or app.models -- is the app package on the PYTHONPATH?  %s",
            exc,
        )
        raise

    engine = create_engine(settings.DATABASE_URL)
    session = SASession(bind=engine)

    try:
        receipt: Receipt | None = session.get(Receipt, receipt_id)
        if receipt is None:
            logger.error("Receipt %d not found in database.", receipt_id)
            return

        logger.info("Processing receipt %d (photo: %s)", receipt_id, receipt.photo_path)

        # 1. Extract fields from the receipt photo
        use_vlm: bool = getattr(settings, "VLM_ENABLED", False)
        extractor = get_extractor(use_vlm=use_vlm)
        fields = extractor.extract_fields(receipt.photo_path)

        # 2. Validate extracted fields (adjusts confidence, adds issues)
        fields = validate_receipt_fields(fields)

        # 3. Persist results back to the receipt row
        receipt.receipt_date = fields.get("datum")  # type: ignore[assignment]
        receipt.total_amount = fields.get("betrag")  # type: ignore[assignment]
        receipt.vat_amount = fields.get("mwst")  # type: ignore[assignment]
        receipt.supplier_name = fields.get("lieferant")  # type: ignore[assignment]
        receipt.receipt_number = fields.get("belegnummer")  # type: ignore[assignment]
        receipt.raw_ocr_text = fields.get("raw_text")  # type: ignore[assignment]
        receipt.field_confidence = fields.get("confidence")  # type: ignore[assignment]
        receipt.status = "done"  # type: ignore[assignment]

        session.commit()
        logger.info(
            "Receipt %d processed successfully. Issues: %s",
            receipt_id,
            fields.get("validation_issues", []),
        )

    except Exception:
        logger.exception("Failed to process receipt %d.", receipt_id)
        try:
            receipt = session.get(Receipt, receipt_id)
            if receipt is not None:
                receipt.status = "failed"  # type: ignore[assignment]
                session.commit()
        except Exception:
            logger.exception("Could not set status=failed on receipt %d.", receipt_id)
        raise
    finally:
        session.close()
        engine.dispose()


# ── ARQ worker settings ──────────────────────────────────────────────
class WorkerSettings:
    """Configuration class consumed by the ``arq`` CLI runner."""

    functions = [process_receipt]

    @staticmethod
    def _build_redis_settings() -> RedisSettings:
        try:
            from app.config import settings as app_settings

            url = app_settings.REDIS_URL
            # Parse redis://host:port into RedisSettings
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return RedisSettings(
                host=parsed.hostname or "localhost",
                port=parsed.port or 6379,
                database=int((parsed.path or "/0").lstrip("/") or "0"),
            )
        except ImportError:
            return RedisSettings()

    redis_settings = _build_redis_settings.__func__()  # type: ignore[attr-defined]
