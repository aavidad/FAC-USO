#!/usr/bin/env python3
"""Prepare source-matched USO Andalucía featured images for the starter package."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
NEWS = ROOT / "data/noticias.json"
MANIFEST = ROOT / "data/news-photos.json"
ORIGINALS = ROOT / "assets/fotos-noticias"
PACKAGE = ROOT / "package/facuso-arranque/theme/assets/noticias"
HOST = "www.usoandalucia.es"
MAX_SOURCE_BYTES = 6 * 1024 * 1024
MAX_OUTPUT_BYTES = 650 * 1024
TIMEOUT = (5, 20)

# The articles below have a visible province/sector spread. Other articles use
# the site's editorial illustration fallback, never a photo from a different event.
SELECTED = {
    "la-justicia-da-la-razon-a-uso-y-obliga-al-sas-a-reactivar-en-un-mes-las-elecciones-sindicales-en-jerez-costa-noroeste-y-sierra-de-cadiz",
    "los-sindicatos-del-opaef-denuncian-el-abandono-institucional-del-presidente-de-la-diputacion-ante-la-grave-crisis-del-servicio-de-recaudacion",
    "uso-andalucia-respalda-las-movilizaciones-del-personal-civil-de-defensa-el-22-de-septiembre-para-exigir-salarios-dignos",
    "caos-en-el-sas-sanidad-uso-denuncie-la-precarizacion-y-el-bloqueo-en-la-bolsa-laboral",
    "uso-denuncia-graves-fallos-de-seguridad-y-casi-30-deficiencias-en-la-nueva-jefatura-de-policia-local-de-isla-cristina",
    "sevilla-sale-a-la-calle-el-personal-civil-de-defensa-reclama-salarios-justos-y-la-eliminacion-de-la-discriminacion-retributiva",
    "uso-andalucia-respalda-la-gran-movilizacion-de-la-plantilla-de-sadeco-ante-el-ayuntamiento-contra-el-desgobierno-y-la-falta-de-medios",
    "fac-uso-y-aplage-llaman-a-movilizarse-en-92-centros-de-defensa-para-exigir-300-euros-consolidados-al-personal-civil",
    "la-plantilla-de-faisem-se-levanta-en-sevilla-tras-15-anos-de-paralisis-laboral-y-la-perdida-de-200-empleos",
    "fac-uso-andalucia-reclama-en-el-parlamento-la-reclasificacion-de-los-tcae-y-alerta-del-desmantelamiento-del-sas-por-las-externalizaciones",
    "fac-uso-andalucia-denuncia-el-acuerdo-de-carrera-profesional-en-las-universidades-por-trato-discriminatorio",
    "i-convenio-sanidad-privada-huelva-firma-historica-y-mejoras-uso",
    "fac-uso-andalucia-lanza-formacion-gratuita-para-policias-y-bomberos-solo-comunidad-andaluza",
    "logro-historico-uso-tumba-en-los-tribunales-la-exclusion-injusta-de-una-trabajadora-en-la-diputacion-de-cordoba",
    "uso-y-aplage-vuelven-a-la-calle-en-andalucia-para-exigir-un-acuerdo-retributivo-justo-para-todo-el-personal-civil-de-defensa",
    "exito-rotundo-de-las-movilizaciones-de-las-tcae-en-andaluciafac-uso-llena-los-centros-sanitarios-para-exigir-el-paso-al-grupo-c",
    "uso-denuncia-deficiencias-y-riesgos-en-los-nuevos-quirofanos-del-hospital-de-riotinto",
    "el-comite-de-empresa-de-aucorsa-reclama-en-pleno-municipal-soluciones-urgentes-para-aucorsa-mas-flota-y-condiciones-laborales-dignas",
    "domingo-castillo-respalda-en-sevilla-la-campana-stop-agresiones-de-fac-uso-para-proteger-al-personal-sanitario-y-empleados-publicos",
    "uso-celebra-la-victoria-judicial-frente-al-ayuntamiento-de-moron-por-la-mala-gestion-y-la-falta-de-refuerzos-en-bomberos",
    "fac-uso-andalucia-celebra-un-hito-jornada-laboral-de-4-dias-y-mejoras-sociales-en-el-nuevo-convenio-del-ayuntamiento-de-alcala-la-real",
    "spj-uso-andalucia-marca-la-hoja-de-ruta-para-la-subida-retributiva-del-personal-de-justicia",
    "spj-uso-andalucia-entrega-a-la-consejeria-un-plan-integral-para-mejorar-salarios-derechos-y-condiciones-del-personal-de-justicia",
    "spj-uso-denuncia-una-nueva-caida-del-sistema-informatico-judicial-y-alerta-de-la-exposicion-de-datos-personales",
    "spj-uso-gana-sentencia-clave-contra-la-consejeria-de-justicia-de-la-junta-de-andalucia-por-la-retirada-indebida-de-plazas-en-el-concurso-de-traslados",
}

# Descriptions follow a visual review of the 25 source images. Prefixes are
# checked for uniqueness against the selected article slugs below.
ALT_BY_PREFIX = {
    "la-justicia-da-la-razon": "Cartel de USO sobre la sentencia relativa a las elecciones sindicales del SAS en Jerez.",
    "los-sindicatos-del-opaef": "Cartel de denuncia sindical sobre el servicio de recaudación OPAEF.",
    "uso-andalucia-respalda-las-movilizaciones": "Representantes de USO en una concentración del personal civil de Defensa.",
    "caos-en-el-sas": "Ilustración de personal sanitario en un pasillo hospitalario.",
    "uso-denuncia-graves-fallos": "Infografía sindical sobre las deficiencias de la jefatura de Policía Local de Isla Cristina.",
    "sevilla-sale-a-la-calle": "Participantes en una protesta del personal civil de Defensa con pancartas de USO.",
    "uso-andalucia-respalda-la-gran-movilizacion": "Trabajadores de Sadeco con una pancarta ante un edificio institucional.",
    "fac-uso-y-aplage-llaman": "Participantes en concentraciones del personal civil de Defensa con pancartas sindicales.",
    "la-plantilla-de-faisem": "Representantes de USO en una protesta con banderas sindicales.",
    "fac-uso-andalucia-reclama-en-el-parlamento": "Dos fotografías de reuniones de representantes sindicales en despachos.",
    "fac-uso-andalucia-denuncia-el-acuerdo": "Cartel de FAC-USO sobre la carrera profesional del personal universitario.",
    "i-convenio-sanidad-privada": "Cartel de los sindicatos firmantes del convenio de sanidad privada de Huelva.",
    "fac-uso-andalucia-lanza-formacion": "Cartel de cursos de formación para policías y bomberos.",
    "logro-historico-uso-tumba": "Gráfico sindical sobre una sentencia de la Diputación de Córdoba.",
    "uso-y-aplage-vuelven": "Participantes en una concentración del personal civil de Defensa con pancartas.",
    "exito-rotundo-de-las-movilizaciones": "Gráfico de FAC-USO sobre las movilizaciones de TCAE en Andalucía.",
    "uso-denuncia-deficiencias-y-riesgos": "Exterior del Hospital de Riotinto, en Huelva.",
    "el-comite-de-empresa-de-aucorsa": "Participantes en una concentración con una pancarta sobre la flota de AUCORSA.",
    "domingo-castillo-respalda": "Representantes de USO ante una mesa informativa sobre la campaña contra las agresiones.",
    "uso-celebra-la-victoria": "Gráfico de USO sobre una sentencia relativa a los bomberos de Morón.",
    "fac-uso-andalucia-celebra-un-hito": "Reunión de representantes sindicales en una sala.",
    "spj-uso-andalucia-marca": "Cartel de SPJ-USO sobre retribuciones del personal de Justicia.",
    "spj-uso-andalucia-entrega": "Cartel de SPJ-USO sobre propuestas entregadas a la Consejería de Justicia.",
    "spj-uso-denuncia-una-nueva": "Cartel de SPJ-USO sobre incidencias del sistema informático Adriano.",
    "spj-uso-gana-sentencia": "Gráfico de última hora publicado por SPJ-USO.",
}


def alt_for(slug: str) -> str:
    matches = [alt for prefix, alt in ALT_BY_PREFIX.items() if slug.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Missing or ambiguous visual description: {slug}")
    return matches[0]


def allowed_url(value: str, *, media: bool = False) -> bool:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != HOST or parsed.port is not None:
        return False
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return False
    return not media or parsed.path.startswith("/wp-content/uploads/")


def download(session: requests.Session, url: str) -> bytes:
    if not allowed_url(url, media=True):
        raise ValueError(f"Media URL outside allowlist: {url}")
    with session.get(url, timeout=TIMEOUT, stream=True, allow_redirects=False) as response:
        response.raise_for_status()
        if response.headers.get("Content-Type", "").split(";", 1)[0].lower() not in {
            "image/jpeg", "image/png", "image/webp",
        }:
            raise ValueError(f"Unexpected image type: {url}")
        size = int(response.headers.get("Content-Length", "0"))
        if size > MAX_SOURCE_BYTES:
            raise ValueError(f"Image exceeds {MAX_SOURCE_BYTES} bytes: {url}")
        chunks, total = [], 0
        for chunk in response.iter_content(65536):
            total += len(chunk)
            if total > MAX_SOURCE_BYTES:
                raise ValueError(f"Image exceeds {MAX_SOURCE_BYTES} bytes: {url}")
            chunks.append(chunk)
        return b"".join(chunks)


def main() -> None:
    articles = json.loads(NEWS.read_text(encoding="utf-8"))["posts"]
    chosen = [article for article in articles if article["slug"] in SELECTED]
    if len(chosen) != len(SELECTED) or len(chosen) > 25:
        raise RuntimeError("Selection must match 1–25 known news articles")
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    PACKAGE.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; FAC-USO-editorial-preparation/1.0)"})
    result = []
    for article in chosen:
        slug = article["slug"]
        source_url = article["sources"][0]["url"]
        if not allowed_url(source_url):
            raise ValueError(f"Article URL outside allowlist: {source_url}")
        response = session.get(
            f"https://{HOST}/wp-json/wp/v2/posts",
            params={"slug": slug, "_embed": "1"}, timeout=TIMEOUT,
            allow_redirects=False,
        )
        response.raise_for_status()
        posts = response.json()
        if len(posts) != 1 or posts[0].get("slug") != slug:
            raise ValueError(f"Article missing or ambiguous: {slug}")
        post = posts[0]
        if post.get("link", "").rstrip("/") != source_url.rstrip("/"):
            raise ValueError(f"Article link mismatch: {slug}")
        media = post.get("_embedded", {}).get("wp:featuredmedia", [])
        if len(media) != 1 or media[0].get("id") != post.get("featured_media"):
            raise ValueError(f"No unique featured media: {slug}")
        image_url = media[0].get("source_url", "")
        details = media[0].get("media_details", {})
        width, height = details.get("width", 0), details.get("height", 0)
        if not (0 < width <= 5000 and 0 < height <= 5000 and width * height <= 20_000_000):
            raise ValueError(f"Unexpected image dimensions: {slug}")
        image_bytes = download(session, image_url)
        original_ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[
            media[0]["mime_type"]
        ]
        basename = re.sub(r"[^a-z0-9-]", "-", slug[:64]).rstrip("-")
        basename += "-" + hashlib.sha256(slug.encode()).hexdigest()[:8]
        original = ORIGINALS / (basename + original_ext)
        destination = PACKAGE / (basename + ".webp")
        original.write_bytes(image_bytes)
        subprocess.run(
            ["magick", "-limit", "memory", "256MiB", "-limit", "map", "256MiB",
             "-limit", "disk", "256MiB", str(original), "-auto-orient", "-resize", "1200x1200>",
             "-strip", "-quality", "80", str(destination)],
            check=True, timeout=25,
        )
        if destination.stat().st_size > MAX_OUTPUT_BYTES:
            subprocess.run(
                ["magick", "-limit", "memory", "256MiB", "-limit", "map", "256MiB",
                 "-limit", "disk", "256MiB", str(original), "-auto-orient", "-resize", "1000x1000>",
                 "-strip", "-quality", "67", str(destination)],
                check=True, timeout=25,
            )
        if destination.stat().st_size > MAX_OUTPUT_BYTES:
            raise ValueError(f"Compressed image still too large: {slug}")
        result.append({
            "slug": slug,
            "source_url": source_url,
            "file": "noticias/" + destination.name,
            "alt": alt_for(slug),
            "credit": "USO Andalucía",
            "image_url": image_url,
            "date": post["date"],
        })
        print(f"{len(result):2d}/25 {destination.name} {destination.stat().st_size:,} B", flush=True)
    MANIFEST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
