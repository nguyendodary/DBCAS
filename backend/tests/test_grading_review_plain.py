"""Plain-text normalization for administrator prose."""
from app.services.grading_review import _plain


def test_plain_preserves_literal_less_than():
    assert _plain("a < b") == "a < b"
    assert _plain("x<3 and y>2") == "x<3 and y>2"


def test_plain_strips_real_html_tag():
    assert _plain("before <b>bold</b> after") == "before bold after"


def test_plain_strips_nested_and_adjacent_tags():
    assert _plain("<div><span>x</span></div><br/>") == "x"


def test_plain_preserves_unclosed_tag():
    assert _plain("a <div") == "a <div"


def test_plain_empty_input():
    assert _plain("") == ""
