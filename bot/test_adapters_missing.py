"""Offline checks against excerpts of observed official responses."""

import unittest
from datetime import date

try:
    from .adapters_missing import probe_bop_html
except ImportError:
    from adapters_missing import probe_bop_html


# Excerpt from https://app.dipalme.org/bop/publico.zul on 2026-10-18.
ALMERIA_BOOTSTRAP = b'''<!DOCTYPE html>
<html><body><div id="aD3X_" class="z-temp"><div id="zk_proc"
class="z-loading"><div class="z-loading-indicator">Procesando...</div></div></div>
<script class="z-runonce" type="text/javascript">zkmx([0,'aD3X_',{}],9);
window.location.replace(controlarHTTPS('publico.zul', 'publicoValidar.zul'));
</script><noscript><div class="noscript"><p>Sorry, JavaScript must be enabled.
</p></div></noscript></body></html>'''

# Excerpt from https://www.bopmalaga.es/sumario.php?fecha=13-07-2026
# on 2026-10-18.
MALAGA_GATE = '''<!doctype html><html lang="es"><head>
<title>Verificacion necesaria</title>
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
</head><body><main class="turnstile-gate">
<h2>Verificación de seguridad</h2><form method="post" action="/sumario.php?fecha=13-07-2026">
<div class="cf-turnstile" data-sitekey="0x4AAAAAADTRvqBKAdrKzUoZ"></div>
</form></main></body></html>'''.encode()

# Official navigation, which links to Huelva's unresolved BOP host; this is
# not an announcement listing.
HUELVA_NAVIGATION = b'''<nav><a href="https://s2.diphuelva.es/servicios/bope_web/UltimoBop">Ultimo BOP</a>
<a href="https://s2.diphuelva.es/servicios/bope_web/busquedaCalendario">Calendario</a></nav>'''


class ProbeBOPHTMLTests(unittest.TestCase):
    def test_almeria_javascript_bootstrap_is_not_a_daily_listing(self):
        report = probe_bop_html(ALMERIA_BOOTSTRAP, province_slug="almeria",
                                published=date(2026, 10, 15))
        self.assertEqual(report["status"], "javascript_required")
        self.assertFalse(report["enabled"])

    def test_malaga_turnstile_gate_is_not_a_daily_listing(self):
        report = probe_bop_html(MALAGA_GATE, province_slug="malaga",
                                published=date(2026, 7, 13))
        self.assertEqual(report["status"], "verification_required")
        self.assertEqual(report["source_url"],
                         "https://www.bopmalaga.es/sumario.php?fecha=13-07-2026")
        self.assertFalse(report["enabled"])

    def test_huelva_navigation_is_not_an_announcement_listing(self):
        report = probe_bop_html(HUELVA_NAVIGATION, province_slug="huelva",
                                published=date(2026, 10, 15))
        self.assertEqual(report["status"], "layout_unverified")
        self.assertFalse(report["enabled"])

    def test_pdf_is_never_used_as_html(self):
        report = probe_bop_html(b"%PDF-1.7", province_slug="huelva",
                                published=date(2026, 10, 15))
        self.assertEqual(report["status"], "pdf_response")

    def test_oversized_response_is_not_parsed(self):
        report = probe_bop_html(b"x" * 2_000_001, province_slug="malaga",
                                published=date(2026, 10, 15))
        self.assertEqual(report["status"], "response_too_large")


if __name__ == "__main__":
    unittest.main()
