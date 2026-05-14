from app.nlp.intent_preprocessor import preprocess_intent_text
from app.nlp.money_parser import parse_money_amount
from app.nlp.relative_date_parser import parse_relative_date
from app.nlp.vietnamese_normalizer import normalize_vietnamese_text


def test_money_parser_supports_cu_and_ty() -> None:
    assert parse_money_amount("2 củ 6") == 2_600_000
    assert parse_money_amount("1 tỷ 2") == 1_200_000_000


def test_relative_date_parser_supports_hom_kia_and_tuan_sau() -> None:
    assert parse_relative_date("hôm kia") is not None
    assert parse_relative_date("tuần sau") is not None


def test_normalizer_handles_vietnamese_slang() -> None:
    assert "hoa don" in normalize_vietnamese_text("thêm bill điện")
    assert "quan yen tinh" in normalize_vietnamese_text("cafe nào chill gần đây")


def test_preprocessor_marks_continuation_hint() -> None:
    processed = preprocess_intent_text("thêm tiền nước luôn")
    assert processed.hints["continue_previous_flow"] is True
