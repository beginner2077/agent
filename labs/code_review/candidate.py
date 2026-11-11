"""待审查版本：将排序移到初始化，并缓存重复列表查询。"""

from labs.code_review.models import Invoice


class InvoiceService:
    def __init__(self, invoices: tuple[Invoice, ...]):
        self._invoices = tuple(sorted(
            invoices,
            key=lambda invoice: (invoice.issued_on, invoice.number),
            reverse=True,
        ))
        self._cache = {}

    def list_invoices(self, tenant_id, state="all", page=1, page_size=20):
        if state not in {"all", "open", "paid"}:
            raise ValueError("unsupported state")
        if page < 1 or page_size < 1:
            raise ValueError("page and page_size must be positive")

        key = (state, page, page_size)
        if key in self._cache:
            return self._cache[key]

        visible = [
            invoice for invoice in self._invoices
            if invoice.tenant_id == tenant_id
        ]
        start = (page - 1) * page_size
        window = visible[start:start + page_size]
        result = tuple(
            invoice for invoice in window
            if state == "all" or invoice.state == state
        )
        self._cache[key] = result
        return result
