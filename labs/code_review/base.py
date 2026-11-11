"""改动前的列表服务，作为本次审查的比较基线。"""

from labs.code_review.models import Invoice


class InvoiceService:
    def __init__(self, invoices: tuple[Invoice, ...]):
        self._invoices = invoices

    def list_invoices(self, tenant_id, state="all", page=1, page_size=20):
        if state not in {"all", "open", "paid"}:
            raise ValueError("unsupported state")
        if page < 1 or page_size < 1:
            raise ValueError("page and page_size must be positive")

        visible = [
            invoice for invoice in self._invoices
            if invoice.tenant_id == tenant_id
            and (state == "all" or invoice.state == state)
        ]
        visible.sort(key=lambda invoice: (invoice.issued_on, invoice.number), reverse=True)
        start = (page - 1) * page_size
        return tuple(visible[start:start + page_size])
