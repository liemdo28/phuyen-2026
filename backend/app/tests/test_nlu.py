from app.services.nlu import extract_amount, extract_relative_date, heuristic_intent_parse


def test_extract_amount_compact_trieu() -> None:
    assert extract_amount("bill điện 2tr6") == 2_600_000


def test_extract_amount_k() -> None:
    assert extract_amount("thêm chi phí sơn 700k") == 700_000


def test_relative_date_hom_qua() -> None:
    assert extract_relative_date("tìm receipt hôm qua") is not None


def test_intent_detection_expense_create() -> None:
    intent = heuristic_intent_parse("thêm bill điện 2 triệu 6")
    assert intent.intent_type == "create"
    assert intent.domain == "expense"
    assert intent.extracted_fields["amount"] == 2_600_000

