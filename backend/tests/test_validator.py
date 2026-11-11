import datetime

from app.extraction.validator import CONFIDENCE_THRESHOLD, validate_receipt_fields


def _make_fields(**overrides):
    fields = {
        "datum": str(datetime.date.today()),
        "betrag": 119.99,
        "mwst": 20.00,
        "lieferant": "Kaufland Bulgaria",
        "belegnummer": "F-0001234",
        "confidence": {
            "datum": 0.95,
            "betrag": 0.95,
            "mwst": 0.95,
            "lieferant": 0.95,
            "belegnummer": 0.95,
        },
    }
    fields.update(overrides)
    return fields


class TestDatumValidation:
    def test_valid_date_passes(self):
        result = validate_receipt_fields(_make_fields())
        assert result["confidence"]["datum"] >= CONFIDENCE_THRESHOLD
        assert not any("datum" in i for i in result["validation_issues"])

    def test_empty_date_penalised(self):
        result = validate_receipt_fields(_make_fields(datum=""))
        assert result["confidence"]["datum"] < CONFIDENCE_THRESHOLD

    def test_future_date_penalised(self):
        future = str(datetime.date.today() + datetime.timedelta(days=30))
        result = validate_receipt_fields(_make_fields(datum=future))
        assert result["confidence"]["datum"] < CONFIDENCE_THRESHOLD
        assert any("Zukunft" in i for i in result["validation_issues"])

    def test_old_date_penalised(self):
        old = str(datetime.date.today().replace(year=datetime.date.today().year - 3))
        result = validate_receipt_fields(_make_fields(datum=old))
        assert result["confidence"]["datum"] < CONFIDENCE_THRESHOLD
        assert any("2 Jahre" in i for i in result["validation_issues"])

    def test_invalid_format_penalised(self):
        result = validate_receipt_fields(_make_fields(datum="not-a-date"))
        assert result["confidence"]["datum"] < CONFIDENCE_THRESHOLD


class TestBetragValidation:
    def test_valid_amount(self):
        result = validate_receipt_fields(_make_fields(betrag=50.0))
        assert result["confidence"]["betrag"] >= CONFIDENCE_THRESHOLD

    def test_zero_amount_penalised(self):
        result = validate_receipt_fields(_make_fields(betrag=0))
        assert result["confidence"]["betrag"] < CONFIDENCE_THRESHOLD

    def test_negative_amount_penalised(self):
        result = validate_receipt_fields(_make_fields(betrag=-10))
        assert result["confidence"]["betrag"] < CONFIDENCE_THRESHOLD

    def test_huge_amount_penalised(self):
        result = validate_receipt_fields(_make_fields(betrag=200_000))
        assert result["confidence"]["betrag"] < CONFIDENCE_THRESHOLD


class TestMwstValidation:
    def test_valid_20pct_vat(self):
        result = validate_receipt_fields(_make_fields(betrag=120.0, mwst=20.0))
        assert result["confidence"]["mwst"] >= CONFIDENCE_THRESHOLD

    def test_valid_9pct_vat(self):
        result = validate_receipt_fields(_make_fields(betrag=109.0, mwst=9.0))
        assert result["confidence"]["mwst"] >= CONFIDENCE_THRESHOLD

    def test_mwst_greater_than_betrag_penalised(self):
        result = validate_receipt_fields(_make_fields(betrag=50.0, mwst=60.0))
        assert result["confidence"]["mwst"] < CONFIDENCE_THRESHOLD

    def test_implausible_rate_penalised(self):
        result = validate_receipt_fields(_make_fields(betrag=100.0, mwst=50.0))
        assert result["confidence"]["mwst"] < CONFIDENCE_THRESHOLD


class TestLieferantValidation:
    def test_valid_supplier(self):
        result = validate_receipt_fields(_make_fields(lieferant="Lidl"))
        assert result["confidence"]["lieferant"] >= CONFIDENCE_THRESHOLD

    def test_empty_supplier_penalised(self):
        result = validate_receipt_fields(_make_fields(lieferant=""))
        assert result["confidence"]["lieferant"] < CONFIDENCE_THRESHOLD

    def test_single_char_penalised(self):
        result = validate_receipt_fields(_make_fields(lieferant="X"))
        assert result["confidence"]["lieferant"] < CONFIDENCE_THRESHOLD


class TestBelegnummerValidation:
    def test_valid_number(self):
        result = validate_receipt_fields(_make_fields(belegnummer="INV-2024-001"))
        assert result["confidence"]["belegnummer"] >= CONFIDENCE_THRESHOLD

    def test_no_digits_penalised(self):
        result = validate_receipt_fields(_make_fields(belegnummer="ABC"))
        assert result["confidence"]["belegnummer"] < 0.95
        assert any("belegnummer" in i for i in result["validation_issues"])


class TestNoIssuesOnValidReceipt:
    def test_clean_receipt_no_issues(self):
        result = validate_receipt_fields(_make_fields(betrag=120.0, mwst=20.0))
        assert result["validation_issues"] == []
