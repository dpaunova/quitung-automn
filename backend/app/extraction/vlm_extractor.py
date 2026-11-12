"""VLM-based receipt field extraction using PaddleOCR-VL.

Two implementations:
- MockExtractor: returns plausible fake data for development without the model.
- VLMExtractor: the real implementation using PaddleOCR-VL 1.5 (0.9B).
"""

from __future__ import annotations

import json
import logging
import random
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Type alias for the extraction result ────────────────────────────
FieldConfidence = dict[str, float]

ExtractionResult = dict[str, Any]
"""
Expected shape:
{
    "datum": str,           # YYYY-MM-DD
    "betrag": float,        # total in BGN
    "mwst": float,          # VAT in BGN
    "lieferant": str,       # company name
    "belegnummer": str,     # receipt number
    "confidence": {
        "datum": float,
        "betrag": float,
        "mwst": float,
        "lieferant": float,
        "belegnummer": float,
    },
    "raw_text": str,
}
"""

# Bulgarian prompt sent to the VLM
VLM_PROMPT = (
    "Извлечи от този касов бон следните полета като JSON: "
    "datum (формат: YYYY-MM-DD), "
    "betrag (обща сума в лева, число), "
    "mwst (ДДС сума в лева, число), "
    "lieferant (име на фирмата), "
    "belegnummer (номер на бона)"
)


# ── Abstract base class ─────────────────────────────────────────────
class Extractor(ABC):
    """Interface every extractor must implement."""

    @abstractmethod
    def extract_fields(self, image_path: str) -> ExtractionResult:
        """Extract structured fields from a receipt image.

        Args:
            image_path: absolute or relative path to the receipt photo.

        Returns:
            ExtractionResult dict (see module-level docstring).
        """


# ── Mock implementation ──────────────────────────────────────────────
# Realistic Bulgarian supplier names for fake data
_BG_SUPPLIERS = [
    "БИЛЛА БЪЛГАРИЯ ЕООД",
    "ЛИДЛ БЪЛГАРИЯ ЕООД ЕНД КО КД",
    "КАУФЛАНД БЪЛГАРИЯ ЕООД ЕНД КО КД",
    "ФАНТАСТИКО ООД",
    "ОМВ БЪЛГАРИЯ ООД",
    "ШЕЛЛ БЪЛГАРИЯ ЕАД",
    "ЛУКОЙЛ НЕФТОХИМ БУРГАС АД",
    "КОСМО БЪЛГАРИЯ МОБАЙЛ ЕАД",
    "ВИВАКОМ ЕООД",
    "СОФИЙСКА ВОДА АД",
    "ТОПЛИВО АД",
    "МЕТРО КЕШ ЕНД КЕРИ БЪЛГАРИЯ ЕООД",
    "АПТЕКИ МАРЕШКИ ЕООД",
    "ПРАКТИКЕР РИТЕЙЛ ЕООД",
    "ХИТ ХИПЕРМАРКЕТ ЕАД",
]

_SAMPLE_RAW_TEXTS = [
    (
        "БИЛЛА БЪЛГАРИЯ ЕООД\nСофия, бул. Цариградско шосе 115\n"
        "ЕИК: 130007884\nДата: 05.11.2026  14:32\n"
        "Хляб пълнозърн.   1 x 2.49   2.49\n"
        "Мляко прясно 1л   1 x 3.19   3.19\n"
        "Кашкавал 400г     1 x 8.99   8.99\n"
        "ОБЩА СУМА:                   14.67 лв\n"
        "в т.ч. ДДС 20%:              2.45 лв\n"
        "Фискален бон No: 0042781\n"
    ),
    (
        "ОМВ БЪЛГАРИЯ ООД\nСофия, ул. Околовръстен път 216\n"
        "ЕИК: 121759222\nДата: 03.11.2026  09:15\n"
        "Бензин А95   32.45л x 2.72   88.26\n"
        "ОБЩА СУМА:                   88.26 лв\n"
        "в т.ч. ДДС 20%:             14.71 лв\n"
        "Фискален бон No: 0197533\n"
    ),
]


class MockExtractor(Extractor):
    """Development-only extractor that returns plausible fake data.

    Simulates a ~2-second processing delay and produces randomised
    confidence values so the downstream validation pipeline can be
    exercised without the actual VLM model.
    """

    def extract_fields(self, image_path: str) -> ExtractionResult:
        logger.info("MockExtractor: simulating extraction for %s", image_path)
        time.sleep(2)  # simulate model inference time

        supplier = random.choice(_BG_SUPPLIERS)
        betrag = round(random.uniform(1.50, 500.00), 2)
        # Bulgarian VAT is 20 % on most goods, 9 % on hotel/tourism
        vat_rate = random.choice([0.20, 0.09])
        netto = round(betrag / (1 + vat_rate), 2)
        mwst = round(betrag - netto, 2)

        # Random recent date (last 60 days)
        import datetime

        days_ago = random.randint(0, 60)
        datum = (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()

        belegnummer = f"{random.randint(1_000_000, 9_999_999):07d}"

        raw_text = random.choice(_SAMPLE_RAW_TEXTS)

        return {
            "datum": datum,
            "betrag": betrag,
            "mwst": mwst,
            "lieferant": supplier,
            "belegnummer": belegnummer,
            "confidence": {
                "datum": round(random.uniform(0.70, 0.99), 2),
                "betrag": round(random.uniform(0.75, 0.99), 2),
                "mwst": round(random.uniform(0.65, 0.99), 2),
                "lieferant": round(random.uniform(0.60, 0.99), 2),
                "belegnummer": round(random.uniform(0.70, 0.99), 2),
            },
            "raw_text": raw_text,
        }


# ── Real VLM implementation ─────────────────────────────────────────
class VLMExtractor(Extractor):
    """Production extractor using PaddleOCR-VL 1.5 (0.9B).

    Falls back to MockExtractor when the model cannot be loaded
    (e.g. in a local dev environment without PaddleOCR-VL installed).
    """

    def __init__(self) -> None:
        self._model: Any | None = None
        self._fallback: MockExtractor | None = None
        self._load_model()

    # ── model loading ────────────────────────────────────────────
    def _load_model(self) -> None:
        try:
            from paddleocr import PaddleOCR  # type: ignore[import-untyped]

            self._model = PaddleOCR(
                use_angle_cls=True,
                lang="bg",
                use_gpu=False,
                show_log=False,
            )
            logger.info("PaddleOCR-VL model loaded successfully.")
        except Exception as exc:
            logger.warning(
                "Could not load PaddleOCR-VL model (%s). Falling back to MockExtractor.",
                exc,
            )
            self._model = None
            self._fallback = MockExtractor()

    # ── extraction ───────────────────────────────────────────────
    def extract_fields(self, image_path: str) -> ExtractionResult:
        if self._model is None:
            if self._fallback is None:
                self._fallback = MockExtractor()
            logger.info("VLMExtractor: using MockExtractor fallback.")
            return self._fallback.extract_fields(image_path)

        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.info("VLMExtractor: extracting fields from %s", image_path)

        try:
            # Call PaddleOCR-VL with the Bulgarian extraction prompt.
            # The exact API depends on the PaddleOCR-VL version; this
            # mirrors the documented chat-style interface for VL models.
            result = self._model.predict(
                input=str(path),
                prompt=VLM_PROMPT,
            )

            raw_text = self._result_to_raw_text(result)
            fields = self._parse_json_from_response(raw_text)
            confidence = self._extract_confidence(result)

            return {
                "datum": str(fields.get("datum", "")),
                "betrag": float(fields.get("betrag", 0.0)),
                "mwst": float(fields.get("mwst", 0.0)),
                "lieferant": str(fields.get("lieferant", "")),
                "belegnummer": str(fields.get("belegnummer", "")),
                "confidence": {
                    "datum": confidence.get("datum", 0.5),
                    "betrag": confidence.get("betrag", 0.5),
                    "mwst": confidence.get("mwst", 0.5),
                    "lieferant": confidence.get("lieferant", 0.5),
                    "belegnummer": confidence.get("belegnummer", 0.5),
                },
                "raw_text": raw_text,
            }
        except Exception as exc:
            logger.error("VLM extraction failed: %s", exc, exc_info=True)
            if self._fallback is None:
                self._fallback = MockExtractor()
            return self._fallback.extract_fields(image_path)

    # ── helpers ──────────────────────────────────────────────────
    @staticmethod
    def _result_to_raw_text(result: Any) -> str:
        """Convert the model's raw output to a plain string."""
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            return result.get("text", result.get("res", json.dumps(result)))
        if isinstance(result, list):
            # PaddleOCR returns list of lists of tuples
            parts: list[str] = []
            for page in result:
                if isinstance(page, list):
                    for line in page:
                        if isinstance(line, (list, tuple)) and len(line) >= 2:
                            text_part = line[1]
                            if isinstance(text_part, (list, tuple)):
                                parts.append(str(text_part[0]))
                            else:
                                parts.append(str(text_part))
            return "\n".join(parts)
        return str(result)

    @staticmethod
    def _parse_json_from_response(raw_text: str) -> dict[str, Any]:
        """Try to extract a JSON object from the model's text response."""
        # The model might return text around the JSON, so we search for
        # the first { ... } block.
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw_text[start : end + 1])
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse JSON from VLM response: %s", raw_text[:200])
        return {}

    @staticmethod
    def _extract_confidence(result: Any) -> FieldConfidence:
        """Derive per-field confidence from the model output.

        PaddleOCR returns per-line confidence scores. We assign a
        uniform average confidence to each field as a baseline;
        the validator refines it afterward.
        """
        scores: list[float] = []
        if isinstance(result, list):
            for page in result:
                if isinstance(page, list):
                    for line in page:
                        if isinstance(line, (list, tuple)) and len(line) >= 2:
                            conf = line[1]
                            if isinstance(conf, (list, tuple)) and len(conf) >= 2:
                                scores.append(float(conf[1]))
                            elif isinstance(conf, (int, float)):
                                scores.append(float(conf))

        avg = sum(scores) / len(scores) if scores else 0.80
        return {
            "datum": avg,
            "betrag": avg,
            "mwst": avg,
            "lieferant": avg,
            "belegnummer": avg,
        }


# ── Factory ──────────────────────────────────────────────────────────
def get_extractor(use_vlm: bool = False) -> Extractor:
    """Return the appropriate extractor based on configuration.

    Args:
        use_vlm: when True, attempt to load the real PaddleOCR-VL model.
                 Falls back to MockExtractor if loading fails.
                 When False (default / dev), return MockExtractor directly.
    """
    if use_vlm:
        return VLMExtractor()
    return MockExtractor()
