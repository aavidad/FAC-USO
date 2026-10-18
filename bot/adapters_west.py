"""Read-only parsers for the public Cádiz and Córdoba daily BOP HTML pages.

The caller fetches pages with its bounded HTTPS client. These functions never
make requests and accept only links matching the official document layouts.
"""

from __future__ import annotations

from datetime import date
from html import unescape
from html.parser import HTMLParser
import re
from urllib.parse import urljoin, urlparse


CADIZ_INDEX_URL = "https://www.bopcadiz.es/index.html"
CORDOBA_HOST = "bop.dipucordoba.es"
CADIZ_HOST = "www.bopcadiz.es"
_MONTHS = {name: n for n, name in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
_EMPLOYMENT = re.compile(
    r"\b(?:plazas?|aspirantes|oposici[oó]n|oposiciones|proceso selectivo|"
    r"pruebas selectivas|concurso[- ]oposici[oó]n|personal laboral|"
    r"personal funcionario|funcionari[oa]s?|bolsa(?:s)? de (?:empleo|trabajo)|"
    r"oferta (?:p[uú]blica )?de empleo|empleo p[uú]blico|"
    r"selecci[oó]n (?:de |del )?(?:personal|un |una ))\b", re.I)
_CADIZ_PDF = re.compile(
    r"^/export/sites/default/\.boletines_pdf/\d{4}/\d{2}_[^/]+/"
    r"BOP\d+_(\d{2}-\d{2}-\d{2})\.pdf#page=\d+$", re.I)
_CORDOBA_PDF = re.compile(r"^/visor-pdf/(\d{2}-\d{2}-\d{4})/BOP-A-\d{4}-\d+\.pdf$", re.I)
_CADIZ_DAILY = re.compile(r"^/boletin/Boletin-numero-\d+-del-ano-\d{4}/$")
_ENGLISH_DATE = re.compile(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+"
                           r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
                           r"(\d{1,2})\s+\d{2}:\d{2}:\d{2}\s+[A-Z]+\s+(\d{4})\b")


def cordoba_daily_url(published: date) -> str:
    """Verified public daily route; an unpublished day can return an empty page."""
    return "https://" + CORDOBA_HOST + "/dia/" + published.strftime("%d-%m-%Y")


def _date_from_english(raw: str) -> date | None:
    match = _ENGLISH_DATE.search(raw)
    if not match:
        return None
    try:
        return date(int(match[3]), _MONTHS[match[1]], int(match[2]))
    except ValueError:
        return None


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _title(value: str) -> str:
    # Keep a compact headline; neither a long official notice nor its body is copied.
    return " ".join(_text(value).split()[:25])[:300].strip()


def _link(href: str, host: str, pattern: re.Pattern[str], published: date) -> str | None:
    href = unescape(href).strip()
    try:
        parsed = urlparse(urljoin("https://" + host + "/", href))
        if parsed.scheme != "https" or parsed.hostname != host or parsed.port not in (None, 443):
            return None
    except ValueError:  # malformed IPv6/port in source HTML
        return None
    if parsed.username or parsed.password or parsed.query:
        return None
    path = parsed.path + ("#" + parsed.fragment if parsed.fragment else "")
    match = pattern.fullmatch(path)
    if not match:
        return None
    expected = published.strftime("%d-%m-%y" if host == CADIZ_HOST else "%d-%m-%Y")
    if match[1] != expected:
        return None
    return parsed.geturl()


class _CadizParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.date_parts: list[str] = []
        self.in_date = False
        self.in_anchor = False
        self.href = ""
        self.parts: list[str] = []
        self.announcements: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "p" and "fecha" in (a.get("class") or "").split() and not self.date_parts:
            self.in_date = True
        if tag == "a" and a.get("href") and "#page=" in a["href"]:
            self.in_anchor, self.href, self.parts = True, a["href"], []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_anchor:
            self.announcements.append((self.href, _text(" ".join(self.parts))))
            self.in_anchor = False
        if tag == "p" and self.in_date:
            self.in_date = False

    def handle_data(self, data: str) -> None:
        if self.in_date:
            self.date_parts.append(data)
        if self.in_anchor:
            self.parts.append(data)


def parse_cadiz(html_data: bytes, published: date) -> list[dict]:
    """Extract employment announcements from the verified Cádiz daily summary."""
    parser = _CadizParser()
    parser.feed(html_data.decode("utf-8", errors="replace"))
    if _date_from_english(" ".join(parser.date_parts)) != published:
        return []
    items = []
    for href, raw_title in parser.announcements:
        url = _link(href, CADIZ_HOST, _CADIZ_PDF, published)
        if url and _EMPLOYMENT.search(raw_title):
            items.append({"title": _title(raw_title), "url": url,
                          "date": published.isoformat(), "excerpt": "", "source": "bop"})
    return items


class _CordobaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title_parts: list[str] = []
        self.in_notice = False
        self.in_first_p = False
        self.first_p_seen = False
        self.notice_parts: list[str] = []
        self.href = ""
        self.announcements: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "li" and "announcement" in (a.get("class") or "").split():
            self.in_notice, self.first_p_seen = True, False
            self.notice_parts, self.href = [], ""
        if self.in_notice and tag == "p" and not self.first_p_seen:
            self.in_first_p, self.first_p_seen = True, True
        if self.in_notice and tag == "a" and a.get("href"):
            self.href = a["href"]

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "p":
            self.in_first_p = False
        if tag == "li" and self.in_notice:
            self.announcements.append((self.href, _text(" ".join(self.notice_parts))))
            self.in_notice = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_first_p:
            self.notice_parts.append(data)


def parse_cordoba(html_data: bytes, published: date) -> list[dict]:
    """Extract employment announcements from `/dia/DD-MM-YYYY` HTML."""
    parser = _CordobaParser()
    parser.feed(html_data.decode("utf-8", errors="replace"))
    if "del día " + published.strftime("%d-%m-%Y") not in _text(" ".join(parser.title_parts)):
        return []
    items = []
    for href, raw_title in parser.announcements:
        url = _link(href, CORDOBA_HOST, _CORDOBA_PDF, published)
        if url and _EMPLOYMENT.search(raw_title):
            items.append({"title": _title(raw_title), "url": url,
                          "date": published.isoformat(), "excerpt": "", "source": "bop"})
    return items


class _CadizCalendar(HTMLParser):
    def __init__(self, published: date) -> None:
        super().__init__(convert_charrefs=True)
        self.published = published
        self.in_entry = False
        self.entry_href = ""
        self.entry_date: list[str] = []
        self.in_date = False
        self.url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "div" and re.fullmatch(r"element_\d+", a.get("id") or ""):
            self.in_entry, self.entry_href, self.entry_date = True, "", []
        if self.in_entry and tag == "a" and a.get("href"):
            self.entry_href = a["href"]
        if self.in_entry and tag == "p" and "fechaEvento" in (a.get("class") or "").split():
            self.in_date = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "p":
            self.in_date = False
        if tag == "div" and self.in_entry:
            if _date_from_english(" ".join(self.entry_date)) == self.published:
                href = unescape(self.entry_href)
                if _CADIZ_DAILY.fullmatch(href):
                    self.url = urljoin("https://" + CADIZ_HOST, href)
            self.in_entry = False

    def handle_data(self, data: str) -> None:
        if self.in_date:
            self.entry_date.append(data)


def cadiz_daily_url(index_data: bytes, published: date) -> str | None:
    """Resolve a bulletin's URL from the official index calendar; no guessed IDs."""
    parser = _CadizCalendar(published)
    parser.feed(index_data.decode("utf-8", errors="replace"))
    return parser.url
