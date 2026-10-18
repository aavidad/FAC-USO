"""Parse the official Huelva BOP announcement response without fetching PDFs.

The caller POSTs ``tipo=2&fecha=YYYY-MM-DD`` to ``HUELVA_API_URL`` and
passes the bounded response to :func:`parse_huelva`. No network I/O occurs
here; document links are built only under the official HTTPS PDF route.
"""

from __future__ import annotations

from datetime import date
from html.parser import HTMLParser
import json
import re


HUELVA_API_URL = "https://s2.diphuelva.es/lib/bope/anuncios_bop/ajaxAnuncios.php"
HUELVA_PDF_BASE = "https://s2.diphuelva.es/portalweb/bope/anuncios/"
MAX_JSON_BYTES = 2_000_000
MAX_ITEMS = 60

_PDF_PART = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_EMPLOYMENT = re.compile(
    r"\b(?:plazas?|bolsas?(?: de (?:empleo|trabajo))?|"
    r"oferta (?:p[uú]blica )?de empleo|empleo p[uú]blico|"
    r"oposici[oó]n(?:es)?|concurso[- ]oposici[oó]n|"
    r"procesos? selectivos?|pruebas selectivas|"
    r"selecci[oó]n de personal|personal (?:laboral|funcionario)|"
    r"provisi[oó]n de puestos?|listas? (?:provisional(?:es)? |"
    r"definitiv(?:as?|os?) )?de admitid[oa]s?)\b", re.I,
)
_GRANT = re.compile(
    r"\b(?:subvenci[oó]n(?:es)?|ayudas? (?:para|destinadas?|econ[oó]micas?)|"
    r"concesi[oó]n de ayudas?|becas?|incentivos?|bonificaciones?)\b", re.I,
)


class _PlainText(HTMLParser):
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


def _title(raw: object) -> str:
    if not isinstance(raw, str) or len(raw) > 4_000:
        return ""
    parser = _PlainText()
    parser.feed(raw)
    parser.close()
    clean = " ".join(" ".join(parser.parts).split())
    return clean


def _document_url(raw: object) -> str | None:
    if not isinstance(raw, str) or len(raw) > 512 or not raw.lower().endswith(".pdf"):
        return None
    parts = raw.split("/")
    if any(part in {"", ".", ".."} or not _PDF_PART.fullmatch(part) for part in parts):
        return None
    return HUELVA_PDF_BASE + raw


def _valid_id(raw: object) -> bool:
    return (type(raw) is int and 0 < raw < 10**20) or (
        isinstance(raw, str) and 0 < len(raw) <= 20 and raw.isascii()
        and raw.isdecimal() and int(raw) > 0
    )


def parse_huelva(json_data: bytes, published: date) -> list[dict]:
    """Return at most 60 employment notices for the exact requested day.

    Malformed or unverified responses and individual unsafe entries are
    ignored. The function does not download, inspect or paraphrase PDF bodies.
    """
    if (not isinstance(json_data, bytes) or len(json_data) > MAX_JSON_BYTES
            or not isinstance(published, date)):
        return []
    try:
        payload = json.loads(json_data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    if (not isinstance(payload, dict) or payload.get("success") is not True
            or payload.get("TieneAnuncios") is not True
            or payload.get("fecha_publicacion") != published.isoformat()
            or not isinstance(payload.get("Anuncios"), list)):
        return []

    items: list[dict] = []
    seen_ids: set[str] = set()
    for notice in payload["Anuncios"]:
        if not isinstance(notice, dict) or not _valid_id(notice.get("id_anuncio")):
            continue
        ident = str(notice["id_anuncio"])
        if ident in seen_ids:
            continue
        full_title = _title(notice.get("titulo"))
        url = _document_url(notice.get("documento"))
        if (not full_title or not url or _GRANT.search(full_title)
                or not _EMPLOYMENT.search(full_title)):
            continue
        title = " ".join(full_title.split()[:25])[:300].strip()
        seen_ids.add(ident)
        items.append({"title": title, "url": url, "date": published.isoformat(),
                      "excerpt": "", "source": "bop"})
        if len(items) == MAX_ITEMS:
            break
    return items
