"""本练习使用不可变的发票快照，无数据库或网络请求。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Invoice:
    number: str
    tenant_id: str
    state: str
    issued_on: str


SNAPSHOT = (
    Invoice("A-103", "alpha", "open", "2026-11-03"),
    Invoice("A-102", "alpha", "paid", "2026-11-02"),
    Invoice("A-101", "alpha", "open", "2026-11-01"),
    Invoice("B-202", "beta", "open", "2026-11-04"),
    Invoice("B-201", "beta", "paid", "2026-11-03"),
)
