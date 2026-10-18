"""Offline checks for the observed Huelva BOP JSON response fields."""

from datetime import date
import json
import unittest

try:
    from .adapters_huelva import HUELVA_API_URL, HUELVA_PDF_BASE, parse_huelva
except ImportError:
    from adapters_huelva import HUELVA_API_URL, HUELVA_PDF_BASE, parse_huelva


DAY = date(2026, 10, 16)


def response(*notices, day="2026-10-16", success=True, has_announcements=True):
    return json.dumps({"success": success, "TieneAnuncios": has_announcements,
                       "fecha_publicacion": day, "Anuncios": list(notices)}).encode()


def notice(ident=11448, title="Bolsa de Operario de Servicios Múltiples Electricista",
           document="Anuncio_381153_BOP-200_2026.pdf"):
    return {"id_anuncio": ident, "titulo": title, "documento": document}


class HuelvaAdapterTest(unittest.TestCase):
    def test_verified_day_and_official_pdf_route(self):
        self.assertEqual(HUELVA_API_URL,
                         "https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php")
        items = parse_huelva(response(notice()), DAY)
        self.assertEqual(items, [{"title": "Bolsa de Operario de Servicios Múltiples Electricista",
                                  "url": HUELVA_PDF_BASE + "Anuncio_381153_BOP-200_2026.pdf",
                                  "date": "2026-10-16", "excerpt": "", "source": "bop"}])

    def test_mismatched_or_unverified_day_is_empty(self):
        raw = response(notice())
        self.assertEqual(parse_huelva(raw, date(2026, 10, 15)), [])
        self.assertEqual(parse_huelva(response(notice(), day="2026-10-15"), DAY), [])
        self.assertEqual(parse_huelva(response(notice(), success="true"), DAY), [])
        self.assertEqual(parse_huelva(response(notice(), has_announcements=False), DAY), [])
        self.assertEqual(parse_huelva(response(day="2026-10-16", has_announcements=False), DAY), [])

    def test_grants_and_unrelated_notices_are_excluded(self):
        raw = response(
            notice(1, "Subvenciones para la contratación de personal", "grant.pdf"),
            notice(2, "Padrón fiscal del municipio", "taxes.pdf"),
            notice(3, "Una plaza de funcionario " + "del municipio " * 25 +
                   "subvenciones a entidades", "hidden-grant.pdf"),
            notice(11450, "Convocatoria de una plaza de Oficial de Jardinería",
                   "Anuncio_379834_BOP-200_2026.pdf"),
        )
        items = parse_huelva(raw, DAY)
        self.assertEqual(len(items), 1)
        self.assertIn("Jardinería", items[0]["title"])

    def test_unsafe_documents_and_ids_are_discarded(self):
        bad_documents = (
            "../secret.pdf", "2026/../secret.pdf", "/absolute.pdf",
            "https://evil.example/notice.pdf", "//evil.example/notice.pdf",
            "safe%2f..%2fsecret.pdf", "safe\\secret.pdf", "safe.pdf?download=1",
            "safe.pdf#page=1", "safe//notice.pdf", "safe/./notice.pdf",
            "safe.txt",
        )
        cases = [notice(i + 1, "Una plaza de funcionario", document)
                 for i, document in enumerate(bad_documents)]
        cases.extend([notice(None), notice(True), notice(-1), notice("bad")])
        self.assertEqual(parse_huelva(response(*cases), DAY), [])

    def test_response_size_and_result_limit(self):
        self.assertEqual(parse_huelva(b" " * 2_000_001, DAY), [])
        self.assertEqual(parse_huelva(b"not-json", DAY), [])
        raw = response(*(notice(i + 1, "Una plaza de funcionario", f"Anuncio_{i}.pdf")
                         for i in range(70)))
        self.assertEqual(len(parse_huelva(raw, DAY)), 60)


if __name__ == "__main__":
    unittest.main()
