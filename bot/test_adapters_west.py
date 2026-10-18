"""Small offline fragments from the official BOP HTML observed 18 October 2026."""

from datetime import date
import unittest

from adapters_west import (
    CADIZ_INDEX_URL, cadiz_daily_url, cordoba_daily_url,
    parse_cadiz, parse_cordoba,
)


CADIZ = b'''<div class="content detail-page"><p class="fecha">
Fri Oct 16 08:00:00 CEST 2026<span><a href="#">Sumario PDF</a></span></p>
<p><a href="/export/sites/default/.boletines_pdf/2026/10_octubre/BOP200_16-10-26.pdf#page=4"><strong>332.720.- Ayuntamiento de La L\xc3\xadnea de la Concepci\xc3\xb3n.</strong> Rectificaci\xc3\xb3n de bases de la convocatoria de varias plazas vacantes.</a></p>
<p><a href="/export/sites/default/.boletines_pdf/2026/10_octubre/BOP200_16-10-26.pdf#page=3">Aprobaci\xc3\xb3n del padr\xc3\xb3n de tasas municipales.</a></p>
</div>'''

CORDOBA = b'''<title>Bolet\xc3\xadn Oficial de la Provincia de C\xc3\xb3rdoba del d\xc3\xada 16-10-2026</title>
<li class="announcement "><p>Resoluci\xc3\xb3n sobre aspirantes admitidos de 5 plazas de T\xc3\xa9cnico/a Superior Inform\xc3\xa1tico/a</p>
<p class="ps-2"><a class="pdf" href="/visor-pdf/16-10-2026/BOP-A-2026-3423.pdf">PDF BOP-A-2026-3423</a></p></li>
<li class="announcement "><p>Bases de convocatoria de subvenciones culturales</p>
<p><a href="/visor-pdf/16-10-2026/BOP-A-2026-3500.pdf">PDF BOP-A-2026-3500</a></p></li>'''


class AdaptersWestTest(unittest.TestCase):
    def test_cadiz_real_summary_fragment(self):
        result = parse_cadiz(CADIZ, date(2026, 10, 16))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2026-10-16")
        self.assertEqual(result[0]["source"], "bop")
        self.assertEqual(result[0]["excerpt"], "")
        self.assertTrue(result[0]["url"].endswith("BOP200_16-10-26.pdf#page=4"))
        self.assertEqual(parse_cadiz(CADIZ, date(2026, 10, 15)), [])

    def test_cadiz_calendar_resolves_only_verified_day(self):
        html = b'''<div id="element_0" class="resumenEventos">
<h3><a href='/boletin/Boletin-numero-200-del-ano-2026/'>Boletin</a></h3>
<p class="fechaEvento">Fri Oct 16 08:00:00 CEST 2026</p></div>'''
        self.assertEqual(CADIZ_INDEX_URL, "https://www.bopcadiz.es/index.html")
        self.assertEqual(cadiz_daily_url(html, date(2026, 10, 16)),
                         "https://www.bopcadiz.es/boletin/Boletin-numero-200-del-ano-2026/")
        self.assertIsNone(cadiz_daily_url(html, date(2026, 10, 15)))

    def test_cordoba_real_summary_fragment(self):
        self.assertEqual(cordoba_daily_url(date(2026, 10, 16)),
                         "https://bop.dipucordoba.es/dia/16-10-2026")
        result = parse_cordoba(CORDOBA, date(2026, 10, 16))
        self.assertEqual(len(result), 1)
        self.assertIn("plazas", result[0]["title"])
        self.assertEqual(result[0]["url"],
                         "https://bop.dipucordoba.es/visor-pdf/16-10-2026/BOP-A-2026-3423.pdf")
        self.assertEqual(parse_cordoba(CORDOBA, date(2026, 10, 15)), [])

    def test_rejects_off_host_and_wrong_day_documents(self):
        poisoned = CADIZ.replace(b"/export/sites", b"https://evil.example/export/sites", 1)
        self.assertEqual(parse_cadiz(poisoned, date(2026, 10, 16)), [])
        poisoned = CORDOBA.replace(b"/visor-pdf/16-10-2026", b"/visor-pdf/15-10-2026", 1)
        self.assertEqual(parse_cordoba(poisoned, date(2026, 10, 16)), [])


if __name__ == "__main__":
    unittest.main()
