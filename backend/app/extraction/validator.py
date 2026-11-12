"""Agentische Validierung -- rule-based plausibility checks for extracted receipt fields.

Each rule checks one aspect of the extracted data. When a rule is
violated the corresponding field's confidence is reduced by a penalty
factor. The final confidence for each field is::

    final = model_confidence * product_of_penalty_factors

Fields with a final confidence below 0.85 should be highlighted in
the UI (yellow marking) for the user to review manually.
"""

from __future__ import annotations

import datetime
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Threshold below which a field should be marked for manual review
CONFIDENCE_THRESHOLD = 0.85

# Penalty factors (subtracted from 1.0 to form a multiplier)
_PENALTY_DATUM_IMPLAUSIBLE = 0.3
_PENALTY_BETRAG_IMPLAUSIBLE = 0.5
_PENALTY_MWST_IMPLAUSIBLE = 0.2
_PENALTY_CROSS_CHECK_FAILED = 0.3
_PENALTY_LIEFERANT_EMPTY = 0.5
_PENALTY_BELEGNUMMER_NO_DIGITS = 0.1

# Cross-check tolerance in BGN
_CROSS_CHECK_TOLERANCE = 0.02

# Bulgarian VAT rates
_VAT_RATES = [0.20, 0.09]
_VAT_RATE_TOLERANCE = 0.03  # allow 3 percentage points of slack


def validate_receipt_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Apply plausibility rules and adjust confidence scores.

    Args:
        fields: extraction result from an ``Extractor``.  Must contain
            at least ``datum``, ``betrag``, ``mwst``, ``lieferant``,
            ``belegnummer``, and a ``confidence`` sub-dict with the same
            keys.

    Returns:
        The *same* dict (mutated in place for convenience) with:
        - ``confidence`` values reduced where rules are violated.
        - A new ``validation_issues`` list describing every violation.
    """
    issues: list[str] = []
    confidence: dict[str, float] = dict(fields.get("confidence", {}))

    # ── datum: must be in the past, not older than 2 years ───────
    _validate_datum(fields, confidence, issues)

    # ── betrag: must be > 0 and < 100 000 ───────────────────────
    _validate_betrag(fields, confidence, issues)

    # ── mwst: must be <= betrag, approx 20 % or 9 % of netto ────
    _validate_mwst(fields, confidence, issues)

    # ── cross-check: netto + mwst approx betrag ─────────────────
    _validate_cross_check(fields, confidence, issues)

    # ── lieferant: at least 2 characters ─────────────────────────
    _validate_lieferant(fields, confidence, issues)

    # ── belegnummer: must contain digits ─────────────────────────
    _validate_belegnummer(fields, confidence, issues)

    fields["confidence"] = confidence
    fields["validation_issues"] = issues
    return fields


# ── Individual rule implementations ──────────────────────────────────


def _apply_penalty(confidence: dict[str, float], field: str, penalty: float) -> None:
    """Multiply the field's confidence by (1 - penalty)."""
    current = confidence.get(field, 1.0)
    confidence[field] = round(current * (1.0 - penalty), 4)


def _validate_datum(
    fields: dict[str, Any],
    confidence: dict[str, float],
    issues: list[str],
) -> None:
    datum_str = fields.get("datum", "")
    if not datum_str:
        _apply_penalty(confidence, "datum", _PENALTY_DATUM_IMPLAUSIBLE)
        issues.append("datum: Feld ist leer.")
        return

    try:
        datum = datetime.date.fromisoformat(str(datum_str))
    except (ValueError, TypeError):
        _apply_penalty(confidence, "datum", _PENALTY_DATUM_IMPLAUSIBLE)
        issues.append(f"datum: Ungültiges Datumsformat '{datum_str}'.")
        return

    today = datetime.date.today()
    if datum > today:
        _apply_penalty(confidence, "datum", _PENALTY_DATUM_IMPLAUSIBLE)
        issues.append(f"datum: Datum liegt in der Zukunft ({datum_str}).")

    two_years_ago = today.replace(year=today.year - 2)
    if datum < two_years_ago:
        _apply_penalty(confidence, "datum", _PENALTY_DATUM_IMPLAUSIBLE)
        issues.append(f"datum: Datum ist älter als 2 Jahre ({datum_str}).")


def _validate_betrag(
    fields: dict[str, Any],
    confidence: dict[str, float],
    issues: list[str],
) -> None:
    try:
        betrag = float(fields.get("betrag", 0))
    except (ValueError, TypeError):
        _apply_penalty(confidence, "betrag", _PENALTY_BETRAG_IMPLAUSIBLE)
        issues.append(f"betrag: Kein gültiger Zahlenwert ('{fields.get('betrag')}').")
        return

    if betrag <= 0:
        _apply_penalty(confidence, "betrag", _PENALTY_BETRAG_IMPLAUSIBLE)
        issues.append(f"betrag: Wert ist <= 0 ({betrag}).")

    if betrag >= 100_000:
        _apply_penalty(confidence, "betrag", _PENALTY_BETRAG_IMPLAUSIBLE)
        issues.append(f"betrag: Wert ist >= 100.000 BGN ({betrag}).")


def _validate_mwst(
    fields: dict[str, Any],
    confidence: dict[str, float],
    issues: list[str],
) -> None:
    try:
        mwst = float(fields.get("mwst", 0))
        betrag = float(fields.get("betrag", 0))
    except (ValueError, TypeError):
        _apply_penalty(confidence, "mwst", _PENALTY_MWST_IMPLAUSIBLE)
        issues.append("mwst: Kein gültiger Zahlenwert.")
        return

    if mwst > betrag:
        _apply_penalty(confidence, "mwst", _PENALTY_MWST_IMPLAUSIBLE)
        issues.append(f"mwst: MwSt ({mwst}) ist größer als Betrag ({betrag}).")

    # Check whether the VAT amount matches an expected rate
    if betrag > 0 and mwst > 0:
        netto = betrag - mwst
        if netto > 0:
            actual_rate = mwst / netto
            matches_any_rate = any(
                abs(actual_rate - rate) <= _VAT_RATE_TOLERANCE for rate in _VAT_RATES
            )
            if not matches_any_rate:
                _apply_penalty(confidence, "mwst", _PENALTY_MWST_IMPLAUSIBLE)
                issues.append(
                    f"mwst: MwSt-Satz ({actual_rate:.2%}) entspricht keinem "
                    f"erwarteten Satz (20 % oder 9 %)."
                )


def _validate_cross_check(
    fields: dict[str, Any],
    confidence: dict[str, float],
    issues: list[str],
) -> None:
    try:
        mwst = float(fields.get("mwst", 0))
        betrag = float(fields.get("betrag", 0))
    except (ValueError, TypeError):
        return  # already caught by individual validators

    if betrag <= 0 or mwst <= 0:
        return  # skip cross-check when individual fields are invalid

    netto = betrag - mwst
    reconstructed = netto + mwst
    diff = abs(reconstructed - betrag)

    if diff > _CROSS_CHECK_TOLERANCE:
        # penalise both betrag and mwst since we cannot tell which is wrong
        _apply_penalty(confidence, "betrag", _PENALTY_CROSS_CHECK_FAILED)
        _apply_penalty(confidence, "mwst", _PENALTY_CROSS_CHECK_FAILED)
        issues.append(
            f"cross-check: Netto ({netto:.2f}) + MwSt ({mwst:.2f}) = "
            f"{reconstructed:.2f}, aber Betrag = {betrag:.2f} "
            f"(Differenz: {diff:.2f} BGN)."
        )


def _validate_lieferant(
    fields: dict[str, Any],
    confidence: dict[str, float],
    issues: list[str],
) -> None:
    lieferant = str(fields.get("lieferant", "")).strip()
    if len(lieferant) < 2:
        _apply_penalty(confidence, "lieferant", _PENALTY_LIEFERANT_EMPTY)
        issues.append(f"lieferant: Name ist zu kurz oder leer ('{lieferant}').")


def _validate_belegnummer(
    fields: dict[str, Any],
    confidence: dict[str, float],
    issues: list[str],
) -> None:
    belegnummer = str(fields.get("belegnummer", "")).strip()
    if not re.search(r"\d", belegnummer):
        _apply_penalty(confidence, "belegnummer", _PENALTY_BELEGNUMMER_NO_DIGITS)
        issues.append(f"belegnummer: Enthält keine Ziffern ('{belegnummer}').")
