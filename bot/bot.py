#!/usr/bin/env python3
"""Eight isolated provincial collectors feeding reviewed WordPress drafts."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html import escape, unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse, urljoin, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET
from adapters_west import CADIZ_INDEX_URL, cadiz_daily_url, cordoba_daily_url, parse_cadiz, parse_cordoba
from adapters_huelva import HUELVA_API_URL, parse_huelva

PROVINCES = {
    "almeria": "Almería", "cadiz": "Cádiz", "cordoba": "Córdoba",
    "granada": "Granada", "huelva": "Huelva", "jaen": "Jaén",
    "malaga": "Málaga", "sevilla": "Sevilla",
}
NEWS_HOSTS = {"facusoandalucia.es", "www.facusoandalucia.es", "uso.es", "www.uso.es", "www.boe.es", "boe.es"}
BOE_API = "https://www.boe.es/datosabiertos/api/boe/sumario/"
MAX_BYTES = 2_000_000
MAX_POSTS = 60
USER_AGENT = "FAC-USO-Andalucia-Bot/1.0 (+https://facusoandalucia.es/)"
EMPLOYMENT = re.compile(r"\b(convocatoria|proveer|plazas?|oposici[oó]n|proceso selectivo|bolsa(?:s)?(?: de empleo| de trabajo)?|oferta de empleo|empleo p[uú]blico|concurso[- ]oposici[oó]n|selecci[oó]n de personal)\b", re.I)
BOP_EMPLOYMENT = re.compile(r"\b(plazas?|bolsa(?:s)?(?: de empleo| de trabajo)?|oferta de empleo|empleo p[uú]blico|oposici[oó]n|proceso selectivo|selecci[oó]n de personal|lista(?:do)?s? (?:provisional(?:es)? |definitiv(?:a|o)s? )?de admitid|provisi[oó]n de puestos?|personal laboral|personal funcionario|OEP|OPE)\b", re.I)
BOP_EXCLUDE = re.compile(r"^(?:nombramiento de personal|contrataci[oó]n como personal)|acad[eé]mico de n[uú]mero", re.I)
BOE_ID = re.compile(r"^BOE-[AB]-\d{4}-\d+$")


class BotError(Exception):
    pass


class CycleDeadline(Exception):
    pass


def canonical_url(url: str, allowed_hosts: set[str], *, local=False) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise BotError("URL inválida")
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.username or parsed.password or not host:
        raise BotError("URL con usuario, fragmento o dominio inválido")
    if parsed.fragment and not (parsed.path.lower().endswith(".pdf") and re.fullmatch(r"page=\d{1,4}", parsed.fragment)):
        raise BotError("Fragmento URL no permitido")
    if parsed.scheme != "https" and not (local and parsed.scheme == "http" and host in {"127.0.0.1", "localhost", "facuso-importacion-wordpress-1"}):
        raise BotError("La URL requiere HTTPS")
    if host not in allowed_hosts:
        raise BotError("Dominio fuera de la lista permitida: " + host)
    if parsed.port not in (None, 443) and not local:
        raise BotError("Puerto no permitido")
    return url.strip()


class RestrictedRedirect(HTTPRedirectHandler):
    def __init__(self, hosts: set[str], *, local=False):
        self.hosts, self.local = hosts, local

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        canonical_url(newurl, self.hosts, local=self.local)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url: str, allowed_hosts: set[str], *, headers=None, data=None, local=False, opener=None) -> bytes:
    canonical_url(url, allowed_hosts, local=local)
    client = opener or build_opener(RestrictedRedirect(allowed_hosts, local=local))
    request = Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with client.open(request, timeout=12) as response:
            canonical_url(response.url, allowed_hosts, local=local)
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_BYTES:
                raise BotError("Respuesta demasiado grande")
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise BotError("Respuesta demasiado grande")
            return body
    except HTTPError as exc:
        if exc.code == 404:
            return b""
        raise BotError("HTTP " + str(exc.code)) from exc


def text_only(value: str) -> str:
    class Strip(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []

        def handle_data(self, data):
            self.parts.append(data)

    parser = Strip()
    parser.feed(value or "")
    return re.sub(r"\s+", " ", unescape(" ".join(parser.parts))).strip()


def province_in_title(title: str, province: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(province) + r"(?!\w)", title, re.I))


def item_date(raw: str) -> str:
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.date().isoformat()
    except (TypeError, ValueError, IndexError):
        raise BotError("Fecha RSS inválida")


def parse_rss(xml_data: bytes, *, province: str, source: str, allowed_hosts: set[str]) -> list[dict]:
    if b"\x00" in xml_data or b"<!DOCTYPE" in xml_data.upper():
        raise BotError("RSS con DTD no admitido")
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as exc:
        raise BotError("RSS mal formado") from exc
    items = []
    for entry in root.findall(".//item")[:MAX_POSTS]:
        title = " ".join(text_only(entry.findtext("title") or "").split()[:25])
        link = (entry.findtext("link") or "").strip()
        if not title or len(title) > 300 or not province_in_title(title, province):
            continue
        if source == "boe" and not EMPLOYMENT.search(title):
            continue
        try:
            link = canonical_url(link, allowed_hosts)
            published = item_date(entry.findtext("pubDate") or "")
        except BotError:
            continue
        items.append({"title": title, "url": link, "date": published,
                      "excerpt": "", "source": source})
    return items


def parse_boe(xml_data: bytes, *, province: str, published: date) -> list[dict]:
    if not xml_data:
        return []
    if b"\x00" in xml_data or b"<!DOCTYPE" in xml_data.upper():
        raise BotError("Sumario BOE con DTD no admitido")
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as exc:
        raise BotError("Sumario BOE mal formado") from exc
    if root.findtext("./status/code") != "200":
        raise BotError("Respuesta BOE sin estado 200")
    if root.findtext("./data/sumario/metadatos/fecha_publicacion") != published.strftime("%Y%m%d"):
        raise BotError("La fecha del sumario BOE no coincide")
    items = []
    for section in root.findall(".//seccion[@codigo='2B']"):
        for entry in section.findall(".//item"):
            title = text_only(entry.findtext("titulo") or "")
            ident = entry.findtext("identificador") or ""
            link = entry.findtext("url_html") or ""
            if not (title and len(title) <= 300 and province_in_title(title, province) and EMPLOYMENT.search(title) and BOE_ID.match(ident)):
                continue
            try:
                link = canonical_url(link, {"www.boe.es", "boe.es"})
            except BotError:
                continue
            items.append({"title": title, "url": link, "date": published.isoformat(),
                          "excerpt": "", "source": "boe"})
    return items[:MAX_POSTS]


class _BoeTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.in_paragraph = False
        self.hidden = 0
        self.parts = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag == "div":
            if self.depth:
                self.depth += 1
            elif attributes.get("id") == "textoxslt":
                self.depth = 1
        if self.depth and tag == "p" and not self.in_paragraph:
            self.in_paragraph = True
            self.parts = []

    def handle_endtag(self, tag):
        if tag == "p" and self.in_paragraph:
            paragraph = re.sub(r"\s+", " ", " ".join(self.parts)).strip()
            if paragraph:
                self.paragraphs.append(paragraph)
            self.in_paragraph = False
        if tag == "div" and self.depth:
            self.depth -= 1
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if self.depth and self.in_paragraph and not self.hidden:
            self.parts.append(data)


def parse_boe_detail(html_data: bytes, *, identifier: str) -> list[str]:
    if not BOE_ID.fullmatch(identifier) or not html_data or len(html_data) > MAX_BYTES:
        return []
    html_data = html_data.decode("utf-8", errors="replace")
    if identifier not in html_data:
        return []
    parser = _BoeTextParser()
    parser.feed(html_data)
    result = []
    used = 0
    for paragraph in parser.paragraphs:
        if len(result) >= 6 or used >= 2000:
            break
        remaining = 2000 - used
        if len(paragraph) > remaining:
            if remaining < 80:
                break
            paragraph = paragraph[:remaining].rsplit(" ", 1)[0].strip()
        if paragraph:
            result.append(paragraph)
            used += len(paragraph)
    return result


def enrich_boe(item: dict) -> dict:
    if item["source"] != "boe":
        return item
    ident = (parse_qs(urlparse(item["url"]).query).get("id") or [""])[0]
    if not BOE_ID.fullmatch(ident):
        return item
    try:
        raw = fetch(item["url"], {"www.boe.es", "boe.es"})
        paragraphs = parse_boe_detail(raw, identifier=ident)
    except (BotError, OSError) as exc:
        print("Aviso texto BOE: " + str(exc), file=sys.stderr, flush=True)
        paragraphs = []
    return {**item, "boe_paragraphs": paragraphs}


BOP_HOSTS = {
    "granada": "bop.dipgra.es",
    "sevilla": "bopsevilla.dipusevilla.es",
    "jaen": "bop.dipujaen.es",
}


def read_almeria_browser_file(path: str, *, today: date) -> list[dict]:
    """Accept only fresh announcements from the isolated official-site browser."""
    source = Path(path)
    try:
        descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as file:
            if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                raise BotError("Archivo BOP Almería inválido")
            raw = file.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise BotError("Archivo BOP Almería demasiado grande")
        payload = json.loads(raw)
    except FileNotFoundError:
        return []
    except (OSError, ValueError, TypeError) as exc:
        raise BotError("Archivo BOP Almería no válido") from exc
    if not isinstance(payload, dict) or payload.get("schema") != 1 or not isinstance(payload.get("items"), list):
        raise BotError("Esquema BOP Almería inválido")
    try:
        generated = datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00"))
        if generated.tzinfo is None:
            raise ValueError("timezone")
        age = datetime.now(timezone.utc) - generated.astimezone(timezone.utc)
        if age.total_seconds() < -3600 or age.total_seconds() > 172800:
            raise ValueError("stale")
    except (KeyError, AttributeError, ValueError, TypeError) as exc:
        raise BotError("Captura BOP Almería caducada o sin fecha") from exc
    result = []
    for row in payload["items"][:MAX_POSTS]:
        if not isinstance(row, dict) or row.get("source") != "bop":
            continue
        title = text_only(row.get("title", "")) if isinstance(row.get("title"), str) else ""
        if not title or len(title) > 300 or not BOP_EMPLOYMENT.search(title):
            continue
        try:
            published = date.fromisoformat(row.get("date", ""))
            url = canonical_url(row.get("url", ""), {"app.dipalme.org"})
        except (BotError, TypeError, ValueError):
            continue
        if not (today - timedelta(days=7) <= published <= today):
            continue
        if not re.fullmatch(r"/bop/services/manager/edicto/\d{4}/\d+/anuncio\.pdf", urlparse(url).path):
            continue
        result.append({"title": title, "url": url, "date": published.isoformat(),
                       "excerpt": "", "source": "bop"})
    return result


def _html_part(block: str, tag: str, class_name: str) -> str:
    match = re.search(r"<" + tag + r"\b[^>]*class=[\"'][^\"']*\b" + class_name +
                      r"\b[^\"']*[\"'][^>]*>(.*?)</" + tag + r">", block, re.I | re.S)
    return text_only(match.group(1)) if match else ""


def parse_bop_html(html_data: bytes, *, province_slug: str, published: date) -> list[dict]:
    """Parse only three verified official daily summary layouts, never PDF bodies."""
    host = BOP_HOSTS[province_slug]
    html_data = html_data.decode("iso-8859-1" if province_slug == "jaen" else "utf-8", errors="replace")
    day = published.strftime("%d-%m-%Y")
    if province_slug == "jaen":
        blocks = re.findall(r"<article\b[^>]*>(.*?)</article>", html_data, re.I | re.S)
    else:
        blocks = re.findall(r"<li\b[^>]*class=[\"'][^\"']*\belementoListado\b[^\"']*[\"'][^>]*>(.*?)</li>", html_data, re.I | re.S)
    if not blocks:
        return []
    if day not in html_data and published.strftime("%d/%m/%Y") not in html_data:
        raise BotError("Fecha inesperada en BOP " + province_slug)
    result = []
    for block in blocks[:300]:
        if province_slug == "jaen":
            title = _html_part(block, "p", "edicto")
            href = re.search(r"<a\b[^>]*href=[\"']([^\"']*descargarws\.dip[^\"']*)[\"']", block, re.I)
            if not href or "tipo=bop" not in unescape(href.group(1)):
                continue
        else:
            title = _html_part(block, "h3", "titulo_elemento")
            anchor = next((a for a in re.findall(r"<a\b[^>]*>", block, re.I | re.S)
                           if re.search(r"\benlace_elemento\b", a)), "")
            href = re.search(r"\bhref=[\"']([^\"']+)[\"']", anchor, re.I)
        if not title or len(title) > 300 or not href or not BOP_EMPLOYMENT.search(title):
            continue
        try:
            link = canonical_url(urljoin("https://" + host, unescape(href.group(1))), {host})
        except BotError:
            continue
        result.append({"title": title, "url": link, "date": published.isoformat(),
                       "excerpt": "", "source": "bop"})
    return result[:MAX_POSTS]


def fetch_items(province_slug: str, config: dict, *, today=None, opener=None) -> list[dict]:
    province = PROVINCES[province_slug]
    today = today or date.today()
    found = []
    lookback = min(max(int(config.get("boe_lookback_days", 7)), 1), 14)
    for age in range(lookback):
        day = today - timedelta(days=age)
        raw = fetch(BOE_API + day.strftime("%Y%m%d"), {"www.boe.es", "boe.es"},
                    headers={"Accept": "application/xml"}, opener=opener)
        found.extend(parse_boe(raw, province=province, published=day))
    for source in config.get("rss_sources", []):
        if not source.get("enabled", True):
            continue
        name = source["name"]
        url = source["url"]
        hosts = set(source["allowed_hosts"])
        if not hosts or not hosts.issubset(NEWS_HOSTS):
            raise BotError("Dominio RSS no autorizado")
        raw = fetch(url, hosts, opener=opener)
        found.extend(parse_rss(raw, province=province, source=name, allowed_hosts=hosts))
    if province_slug in BOP_HOSTS and config.get("bop_enabled", False):
        host = BOP_HOSTS[province_slug]
        bop_days = min(max(int(config.get("bop_lookback_days", 3)), 1), 7)
        for age in range(bop_days):
            day = today - timedelta(days=age)
            stamp = day.strftime("%d-%m-%Y")
            if province_slug == "jaen":
                url = "https://" + host + "/bop/" + stamp
            else:
                url = "https://" + host + "/publica/consulta-de-bops/buscador/BOP-" + stamp + "/"
            raw = fetch(url, {host}, opener=opener)
            if raw:
                found.extend(parse_bop_html(raw, province_slug=province_slug, published=day))
    if province_slug == "cadiz" and config.get("bop_enabled", False):
        host = "www.bopcadiz.es"
        index = fetch(CADIZ_INDEX_URL, {host}, opener=opener)
        for age in range(min(max(int(config.get("bop_lookback_days", 3)), 1), 7)):
            day = today - timedelta(days=age)
            daily_url = cadiz_daily_url(index, day)
            if daily_url:
                raw = fetch(daily_url, {host}, opener=opener)
                found.extend(parse_cadiz(raw, day))
    if province_slug == "cordoba" and config.get("bop_enabled", False):
        host = "bop.dipucordoba.es"
        for age in range(min(max(int(config.get("bop_lookback_days", 3)), 1), 7)):
            day = today - timedelta(days=age)
            raw = fetch(cordoba_daily_url(day), {host}, opener=opener)
            if raw:
                found.extend(parse_cordoba(raw, day))
    if province_slug == "huelva" and config.get("bop_enabled", False):
        host = "s2.diphuelva.es"
        for age in range(min(max(int(config.get("bop_lookback_days", 3)), 1), 7)):
            day = today - timedelta(days=age)
            body = urlencode({"tipo": "2", "fecha": day.isoformat()}).encode("ascii")
            try:
                raw = fetch(HUELVA_API_URL, {host}, data=body,
                            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, opener=opener)
                found.extend(parse_huelva(raw, day))
            except (BotError, OSError) as exc:
                print("Aviso BOP Huelva: " + str(exc), file=sys.stderr, flush=True)
    if province_slug == "almeria" and os.getenv("ALMERIA_BOP_FILE"):
        try:
            found.extend(read_almeria_browser_file(os.environ["ALMERIA_BOP_FILE"], today=today))
        except BotError as exc:
            print("Aviso BOP Almería: " + str(exc), file=sys.stderr, flush=True)
    return list({post_identity(item): item for item in found
                 if item["source"] != "bop" or not BOP_EXCLUDE.search(item["title"])}.values())[:MAX_POSTS]


def post_identity(item: dict) -> str:
    url = item["url"]
    if item["source"] == "bop" and urlparse(url).hostname == "www.bopcadiz.es":
        notice = re.match(r"^\d{3}\.\d{3}", item["title"])
        return url + "|" + (notice.group(0) if notice else item["title"])
    return url


def slug_for(identity: str, province_slug: str) -> str:
    return "facuso-" + province_slug + "-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def category_slugs(item: dict, province_slug: str) -> list[str]:
    title = item["title"].lower()
    categories = [province_slug]
    if item["source"] in {"boe", "bop"}:
        if re.search(r"\buniversidad (?:de (?:almer[ií]a|c[aá]diz|c[oó]rdoba|granada|huelva|ja[eé]n|m[aá]laga|sevilla)|pablo de olavide|internacional de andaluc[ií]a)\b", title):
            categories += ["administracion-autonomica", "universidades"]
        elif re.search(r"\bservicio andaluz de salud\b|\bhospital\b", title):
            categories.append("sanidad")
        elif re.search(r"\bjunta de andaluc[ií]a\b|\bconsejer[ií]a de\b", title):
            categories.append("administracion-autonomica")
        elif re.search(r"\bministerio de\b|\badministraci[oó]n general del estado\b|\bdelegaci[oó]n del gobierno\b", title):
            categories.append("administracion-general-del-estado")
        elif re.search(r"\bayuntamiento de\b|\bdiputaci[oó]n (?:provincial )?de\b", title):
            categories.append("administracion-local")
        categories.append("empleo-publico")
        if re.search(r"\bbolsa", title):
            categories.append("bolsas-de-trabajo")
        elif re.search(r"\boferta de empleo|\boep\b|\bope\b", title):
            categories.append("ofertas-de-empleo-publico")
        else:
            categories.append("oposiciones")
    elif EMPLOYMENT.search(title):
        categories += ["empleo-publico"]
        if re.search(r"\bbolsa", title):
            categories.append("bolsas-de-trabajo")
        elif re.search(r"\boferta de empleo|\boep\b|\bope\b", title):
            categories.append("ofertas-de-empleo-publico")
        else:
            categories.append("oposiciones")
    else:
        categories.append("accion-sindical")
    return categories


def post_payload(item: dict, province_slug: str, category_ids: dict[str, int], status: str) -> dict:
    missing = [slug for slug in category_slugs(item, province_slug) if slug not in category_ids]
    if missing:
        raise BotError("Faltan categorías WordPress: " + ", ".join(missing))
    title = item["title"]
    source_name = {"boe": "Boletín Oficial del Estado", "bop": "Boletín Oficial de la Provincia", "fac": "FAC-USO Andalucía", "uso": "USO"}.get(item["source"], item["source"])
    source_url = item["url"]
    intro = f"<p>Publicado por {escape(source_name)} el {escape(item['date'])}.</p>"
    if item["excerpt"]:
        intro += "<p>" + escape(item["excerpt"]) + "</p>"
    if item.get("boe_paragraphs"):
        intro += "<p>Texto del anuncio oficial (BOE):</p>"
        intro += "".join("<p>" + escape(paragraph) + "</p>" for paragraph in item["boe_paragraphs"])
    intro += '<p><a href="' + escape(source_url, quote=True) + '">Consultar la publicación original</a></p>'
    identity = post_identity(item)
    return {"title": escape(title, quote=False), "slug": slug_for(identity, province_slug), "status": status,
            "content": intro, "excerpt": item["excerpt"],
            "comment_status": "closed", "ping_status": "closed",
            "date": item["date"] + "T12:00:00",
            "categories": [category_ids[x] for x in category_slugs(item, province_slug)],
            "meta": {"facuso_source_url": source_url, "facuso_external_id": slug_for(identity, province_slug)}}


class WordPress:
    def __init__(self, base: str, user: str, password: str, *, opener=None):
        parsed = urlparse(base)
        self.host = (parsed.hostname or "").lower()
        self.local = self.host in {"localhost", "127.0.0.1"} or (
            os.getenv("WP_ALLOW_LOCAL_HTTP", "false").lower() == "true"
            and self.host == "facuso-importacion-wordpress-1")
        self.base = canonical_url(base.rstrip("/"), {self.host}, local=self.local) + "/wp-json/wp/v2"
        self.user, self.password = user, password
        self.opener = opener or build_opener(NoRedirect())

    def request(self, endpoint: str, *, params=None, payload=None):
        url = self.base + endpoint + ("?" + urlencode(params) if params else "")
        canonical_url(url, {self.host}, local=self.local)
        token = __import__("base64").b64encode((self.user + ":" + self.password).encode()).decode()
        data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
        request = Request(url, data=data, headers={"Authorization": "Basic " + token,
                           "Content-Type": "application/json", "User-Agent": USER_AGENT},
                          method="POST" if data is not None else "GET")
        try:
            with self.opener.open(request, timeout=12) as response:
                canonical_url(response.url, {self.host}, local=self.local)
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise BotError("Respuesta WordPress demasiado grande")
                return json.loads(body)
        except HTTPError as exc:
            if exc.code == 400 and payload is None and params and params.get("page", 1) > 1:
                try:
                    if json.loads(exc.read(2048)).get("code") == "rest_post_invalid_page_number":
                        return []
                except (ValueError, AttributeError):
                    pass
            raise BotError("WordPress HTTP " + str(exc.code) + " en " + endpoint) from exc

    def categories(self) -> dict[str, int]:
        result = {}
        for page in range(1, 10):
            rows = self.request("/categories", params={"per_page": 100, "page": page})
            if not rows:
                break
            result.update({x["slug"]: x["id"] for x in rows})
            if len(rows) < 100:
                break
        return result

    def existing_records(self, province_id: int) -> set[tuple[str, str]]:
        result = set()
        for page in range(1, 11):
            rows = self.request("/posts", params={"context": "edit", "status": "any", "per_page": 100, "page": page})
            if not rows:
                break
            for row in rows:
                source_url = (row.get("meta") or {}).get("facuso_source_url")
                if source_url and province_id in row.get("categories", []):
                    title_field = row.get("title") or {}
                    title = title_field.get("raw") or title_field.get("rendered") or ""
                    result.add((source_url, text_only(title)))
            if len(rows) < 100:
                break
        return result

    def slug_exists(self, slug: str) -> bool:
        rows = self.request("/posts", params={"context": "edit", "status": "any", "slug": slug, "per_page": 100})
        return bool(rows)

    def own_posts(self) -> list[dict]:
        me = self.request("/users/me", params={"context": "edit"})
        user_id = me["id"]
        result = []
        for page in range(1, 11):
            rows = self.request("/posts", params={"context": "edit", "status": "any", "per_page": 100, "page": page})
            result.extend(row for row in rows if row.get("author") == user_id)
            if len(rows) < 100:
                break
        return result


def run(province: str, config: dict, *, dry_run: bool, publish: bool, today=None, wp=None, items=None) -> dict:
    items = items if items is not None else fetch_items(province, config, today=today)
    results = {"province": province, "fetched": len(items), "created": 0, "existing": 0, "preview": 0}
    if dry_run:
        results["preview"] = len(items)
        return results
    if wp is None:
        secret_file = Path(os.environ["WP_APP_PASSWORD_FILE"])
        if not secret_file.is_file():
            raise BotError("Falta el archivo secreto WordPress")
        wp = WordPress(os.environ["WP_BASE_URL"], os.environ["WP_USER"], secret_file.read_text().strip())
    categories = wp.categories()
    if province not in categories:
        raise BotError("Falta la categoría territorial " + province)
    records = wp.existing_records(categories[province])
    urls = {url for url, _ in records}
    for item in items:
        shared_pdf_page = item["source"] == "bop" and urlparse(item["url"]).hostname == "www.bopcadiz.es"
        known = (item["url"], item["title"]) in records if shared_pdf_page else item["url"] in urls
        if known or wp.slug_exists(slug_for(post_identity(item), province)):
            results["existing"] += 1
            continue
        item = enrich_boe(item)
        payload = post_payload(item, province, categories, "publish" if publish else "draft")
        wp.request("/posts", payload=payload)
        urls.add(item["url"])
        records.add((item["url"], item["title"]))
        results["created"] += 1
    return results


def enrich_existing(province: str, wp: WordPress, *, dry_run: bool = False) -> dict:
    categories = wp.categories()
    result = {"province": province, "checked": 0, "updated": 0, "preview": 0,
              "manual_skipped": 0, "protected_categories": 0, "closed_only": 0}
    for row in wp.own_posts():
        result["checked"] += 1
        meta = row.get("meta") or {}
        url = meta.get("facuso_source_url") or ""
        external_id = meta.get("facuso_external_id") or ""
        if not url or not external_id or row.get("slug") != external_id:
            continue
        if categories.get(province) not in row.get("categories", []):
            continue
        needs_close = row.get("comment_status") != "closed" or row.get("ping_status") != "closed"
        raw = (row.get("content") or {}).get("raw") or ""
        match = re.match(r"^<p>Publicado por [^<]+ el (\d{4}-\d{2}-\d{2})\.</p>", raw)
        if not match:
            result["manual_skipped"] += 1
            if needs_close:
                if dry_run:
                    result["preview"] += 1
                else:
                    wp.request("/posts/" + str(row["id"]), payload={"comment_status": "closed",
                               "ping_status": "closed", "categories": row["categories"]})
                    result["closed_only"] += 1
            continue
        try:
            date.fromisoformat(match.group(1))
            url = canonical_url(url, {urlparse(url).hostname or ""})
        except (BotError, ValueError):
            continue
        host = urlparse(url).hostname
        source = "boe" if host in {"www.boe.es", "boe.es"} else (
            "fac" if host in {"facusoandalucia.es", "www.facusoandalucia.es"} else (
                "uso" if host in {"uso.es", "www.uso.es"} else "bop"))
        title_field = row.get("title") or {}
        title = text_only(title_field.get("raw") or title_field.get("rendered") or "")
        item = {"title": title, "url": url, "date": match.group(1), "excerpt": "", "source": source}
        baseline = post_payload(item, province, categories, row.get("status", "draft"))
        if raw != baseline["content"]:
            result["manual_skipped"] += 1
            if needs_close:
                if dry_run:
                    result["preview"] += 1
                else:
                    wp.request("/posts/" + str(row["id"]), payload={"comment_status": "closed",
                               "ping_status": "closed", "categories": row["categories"]})
                    result["closed_only"] += 1
            continue
        item = enrich_boe(item)
        target = post_payload(item, province, categories, row.get("status", "draft"))
        current_categories = row.get("categories", [])
        if source in {"boe", "bop"}:
            matter_slugs = [slug for slug in category_slugs(item, province)
                            if slug in {"empleo-publico", "bolsas-de-trabajo", "oposiciones", "ofertas-de-empleo-publico"}]
            legacy_slugs = [province, "administracion-local", *matter_slugs]
            legacy_categories = [categories[slug] for slug in legacy_slugs]
        else:
            legacy_categories = target["categories"]
        if sorted(current_categories) != sorted(legacy_categories):
            target["categories"] = current_categories
            result["protected_categories"] += 1
        if raw == target["content"] and sorted(current_categories) == sorted(target["categories"]) and not needs_close:
            continue
        if dry_run:
            result["preview"] += 1
            continue
        wp.request("/posts/" + str(row["id"]), payload={"content": target["content"],
                   "categories": target["categories"], "comment_status": "closed",
                   "ping_status": "closed"})
        result["updated"] += 1
    return result


def main():
    parser = argparse.ArgumentParser(description="Noticias provinciales FAC-USO para WordPress")
    parser.add_argument("--province", required=True, choices=PROVINCES)
    parser.add_argument("--config", default=str(Path(__file__).with_name("sources.json")))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish", action="store_true", help="Publicar sin revisión editorial")
    parser.add_argument("--enrich-existing", action="store_true", help="Completar texto BOE y corregir categorías de noticias propias sin tocar ediciones manuales")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=3600)
    args = parser.parse_args()
    if args.interval < 3600:
        parser.error("--interval debe ser al menos 3600 segundos")
    publish = args.publish or os.getenv("BOT_PUBLISH", "false").lower() in {"1", "true", "yes"}
    config = json.loads(Path(args.config).read_text())
    def timeout_handler(signum, frame):
        raise CycleDeadline("Tiempo máximo de ciclo superado (300 s)")
    signal.signal(signal.SIGALRM, timeout_handler)
    if args.enrich_existing:
        try:
            signal.alarm(300)
            secret_file = Path(os.environ["WP_APP_PASSWORD_FILE"])
            wp = WordPress(os.environ["WP_BASE_URL"], os.environ["WP_USER"], secret_file.read_text().strip())
            print(json.dumps(enrich_existing(args.province, wp, dry_run=args.dry_run), ensure_ascii=False), flush=True)
            return 0
        except CycleDeadline as exc:
            print("Error en " + args.province + ": " + str(exc), file=sys.stderr, flush=True)
            return 1
        finally:
            signal.alarm(0)
    while True:
        try:
            signal.alarm(300)
            print(json.dumps(run(args.province, config["provinces"][args.province],
                                 dry_run=args.dry_run, publish=publish), ensure_ascii=False), flush=True)
        except (BotError, CycleDeadline, KeyError, OSError, ValueError) as exc:
            print("Error en " + args.province + ": " + str(exc), file=sys.stderr, flush=True)
            if not args.loop:
                return 1
        finally:
            signal.alarm(0)
        if not args.loop:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
