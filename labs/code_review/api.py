"""未改动的调用方示例：进程内所有租户共用一个服务实例。"""

from dataclasses import asdict, dataclass

from labs.code_review.candidate import InvoiceService
from labs.code_review.models import SNAPSHOT


@dataclass(frozen=True)
class Actor:
    tenant_id: str


SERVICE = InvoiceService(SNAPSHOT)


def list_for_actor(actor: Actor, state="all", page=1, page_size=20):
    invoices = SERVICE.list_invoices(actor.tenant_id, state, page, page_size)
    return {"items": [asdict(invoice) for invoice in invoices]}
