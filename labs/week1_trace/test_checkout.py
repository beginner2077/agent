import pytest

from .pricing import calculate_total
from .receipt import render_receipt


def test_total_without_discount():
    assert calculate_total([1200, 800]) == 2000


def test_total_with_discount():
    assert calculate_total([1200, 800], discount_cents=300) == 1700


def test_discount_cannot_make_total_negative():
    assert calculate_total([500], discount_cents=800) == 0


def test_negative_discount_is_rejected():
    with pytest.raises(ValueError):
        calculate_total([500], discount_cents=-100)


def test_receipt_with_discount():
    assert render_receipt([1200, 800], discount_cents=300) == "Total: 1700 cents"


def test_empty_receipt():
    assert render_receipt([]) == "Total: 0 cents"
