"""已有冒烟用例；不声称覆盖全部业务约束。"""

import unittest

from labs.code_review.candidate import InvoiceService
from labs.code_review.models import SNAPSHOT


class ExistingTests(unittest.TestCase):
    def setUp(self):
        self.service = InvoiceService(SNAPSHOT)

    def test_all_first_page(self):
        result = self.service.list_invoices("alpha", page_size=2)
        self.assertEqual([item.number for item in result], ["A-103", "A-102"])

    def test_open_with_large_page(self):
        result = self.service.list_invoices("alpha", state="open", page_size=10)
        self.assertEqual([item.number for item in result], ["A-103", "A-101"])

    def test_empty_tenant(self):
        self.assertEqual(self.service.list_invoices("empty"), ())

    def test_invalid_state(self):
        with self.assertRaises(ValueError):
            self.service.list_invoices("alpha", state="deleted")

    def test_invalid_page(self):
        with self.assertRaises(ValueError):
            self.service.list_invoices("alpha", page=0)
