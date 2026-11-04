from .pricing import calculate_total


def render_receipt(prices, discount_cents=0):
    return f"Total: {calculate_total(prices, discount_cents=discount_cents)} cents"
