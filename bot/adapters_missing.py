"""Read-only probes for BOP layouts that cannot yet be safely extracted.

These probes do not fetch pages or enable a source.  As checked on 2026-10-18:

* Almería's public entry point returns a ZK JavaScript bootstrap, not the
  rendered announcement table: https://app.dipalme.org/bop/publico.zul
* Huelva's HTML navigation was not directly extractable; its separate JSON
  endpoint was subsequently verified and is implemented in adapters_huelva.py.
* Málaga's indexed daily summaries have an HTML URL, but a direct request
  currently returns a Turnstile gate:
  https://www.bopmalaga.es/sumario.php?fecha=13-07-2026

The HTML probes remain disabled. Huelva uses its official JSON endpoint.
"""

from __future__ import annotations

from datetime import date
from html.parser import HTMLParser


SOURCE_URLS = {
    "almeria": "https://app.dipalme.org/bop/publico.zul",
    "huelva": "https://s2.diphuelva.es/servicios/bope_web/UltimoBop",
    "malaga": "https://www.bopmalaga.es/sumario.php",
}
MAX_HTML_BYTES = 2_000_000


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def probe_bop_html(html_data: bytes, *, province_slug: str, published: date) -> dict:
    """Report whether raw official HTML can support an announcement extractor.

    This is deliberately a probe, not an item parser.  ``enabled`` remains
    false until a real daily response and its links have been verified.
    """
    if province_slug not in SOURCE_URLS:
        raise ValueError(f"Unsupported BOP province: {province_slug}")
    if not isinstance(html_data, bytes):
        raise TypeError("html_data must be bytes")
    if not isinstance(published, date):
        raise TypeError("published must be a date")

    if len(html_data) > MAX_HTML_BYTES:
        status = "response_too_large"
    elif not html_data.strip():
        status = "empty_response"
    elif html_data.startswith(b"%PDF-"):
        status = "pdf_response"
    else:
        raw = html_data.decode("utf-8", errors="replace")
        text_parser = _VisibleText()
        text_parser.feed(raw)
        text_parser.close()
        visible = " ".join(" ".join(text_parser.parts).split()).casefold()
        lower = raw.casefold()

        if province_slug == "almeria" and (
            "zkmx(" in lower or "publicovalidar.zul" in lower
            or "sorry, javascript must be enabled" in visible
        ):
            status = "javascript_required"
        elif province_slug == "malaga" and (
            "challenges.cloudflare.com/turnstile" in lower
            or "cf-turnstile" in lower or "verificación de seguridad" in visible
        ):
            status = "verification_required"
        else:
            status = "layout_unverified"

    source_url = SOURCE_URLS[province_slug]
    if province_slug == "malaga":
        source_url += "?fecha=" + published.strftime("%d-%m-%Y")

    return {
        "province": province_slug,
        "date": published.isoformat(),
        "source_url": source_url,
        "status": status,
        "enabled": False,
    }
