"""A partial rename left one caller using the old function name."""


def calculate_total(prices, discount_cents=0):
    if discount_cents < 0:
        raise ValueError("discount_cents must be non-negative")
    return max(0, sum(prices) - discount_cents)
