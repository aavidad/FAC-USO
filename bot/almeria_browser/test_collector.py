import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from collector import allowed_request, business_days, parse_row, write_atomic


class CollectorTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parent / "fixtures" / "rows_2026-10-15.json"
        self.rows = json.loads(path.read_text(encoding="utf-8"))
        self.day = date(2026, 10, 15)

    def test_official_rows_and_public_pdf_urls(self):
        items = [parse_row(row, self.day) for row in self.rows]
        self.assertEqual([item["url"] for item in items if item], [
            "https://app.dipalme.org/bop/services/manager/edicto/2026/2792/anuncio.pdf",
            "https://app.dipalme.org/bop/services/manager/edicto/2026/2765/anuncio.pdf",
        ])
        self.assertEqual(items[0]["date"], "2026-10-15")
        self.assertIsNone(items[2])

    def test_rejects_stale_and_mismatched_edition(self):
        self.assertIsNone(parse_row(self.rows[0], date(2026, 10, 16)))
        row = self.rows[0].copy()
        row[0] = "2025/200"
        self.assertIsNone(parse_row(row, self.day))

    def test_three_latest_business_days(self):
        self.assertEqual(business_days(date(2026, 10, 18)), [
            date(2026, 10, 16), date(2026, 10, 15), date(2026, 10, 14)])

    def test_network_gate(self):
        self.assertTrue(allowed_request("https://app.dipalme.org/bop/publico.zul"))
        self.assertFalse(allowed_request("https://evil.example/bop/publico.zul"))
        self.assertFalse(allowed_request("http://app.dipalme.org/bop/publico.zul"))
        self.assertFalse(allowed_request("https://app.dipalme.org.evil.example/bop/publico.zul"))
        self.assertFalse(allowed_request("https://app.dipalme.org/other"))

    def test_atomic_json_contract(self):
        item = parse_row(self.rows[0], self.day)
        with TemporaryDirectory() as directory:
            output = Path(directory) / "almeria_bop.json"
            write_atomic([item], output)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], 1)
            self.assertEqual(payload["items"], [item])
            self.assertFalse(output.with_name(output.name + ".tmp").exists())


if __name__ == "__main__":
    unittest.main()
