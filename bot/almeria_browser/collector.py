#!/usr/bin/env python3
"""Collect public employment notices from the official Almería BOP summary."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

PUBLIC_URL = "https://app.dipalme.org/bop/publico.zul"
OUTPUT = Path("/data/almeria_bop.json")
MAX_ITEMS = 20
MAX_ROWS = 100
MAX_JSON_BYTES = 100_000
MAX_RESPONSE_BYTES = 2_000_000
EMPLOYMENT = re.compile(
    r"\b(?:plazas?|bolsa(?:s)?(?: de (?:empleo|trabajo))?|oposici[oó]n|"
    r"concurso[- ]oposici[oó]n|empleo p[uú]blico|proceso selectivo|"
    r"selecci[oó]n de personal|provisi[oó]n de puestos?|"
    r"admitidos?(?:/as)?|oferta p[uú]blica de empleo)\b", re.I
)
BOP_NUMBER = re.compile(r"^\d{4}/\d{1,4}$")
EDICT = re.compile(r"^(\d{1,7})-(\d{4})$")


def business_days(today: date, count: int = 3) -> list[date]:
    result = []
    day = today
    while len(result) < count:
        if day.weekday() < 5:
            result.append(day)
        day -= timedelta(days=1)
    return result


def parse_row(cells: list[str], day: date) -> dict | None:
    """Reject stale results and rows without a verifiable bulletin and edict."""
    if len(cells) != 7 or not BOP_NUMBER.fullmatch(cells[0].strip()):
        return None
    try:
        published = datetime.strptime(cells[1].strip(), "%d/%m/%Y").date()
    except ValueError:
        return None
    if published != day:
        return None
    bop_year = int(cells[0].split("/")[0])
    match = EDICT.fullmatch(cells[5].strip())
    if not match or int(match.group(2)) != bop_year or bop_year != day.year:
        return None
    lines = [" ".join(part.split()) for part in cells[4].splitlines() if part.strip()]
    if len(lines) < 2:
        return None
    headline = lines[-1]
    if not EMPLOYMENT.search(headline):
        return None
    agency = lines[1] if lines[0].upper().startswith("ADMINISTRACIÓN ") else lines[-2]
    title = f"{agency}: {headline}"
    if len(title) > 300:
        title = headline
    if not title or len(title) > 300:
        return None
    edict_id = int(match.group(1))
    url = f"https://app.dipalme.org/bop/services/manager/edicto/{bop_year}/{edict_id}/anuncio.pdf"
    return {"title": title, "url": url, "date": day.isoformat(), "excerpt": "", "source": "bop"}


def allowed_request(url: str) -> bool:
    parsed = urlparse(url)
    return (parsed.scheme == "https" and parsed.hostname == "app.dipalme.org"
            and parsed.port in (None, 443) and not parsed.username and not parsed.password
            and parsed.path.startswith("/bop/"))


def guard_route(route, allowed=allowed_request) -> None:
    """Fetch one permitted URL only; a 3xx never reaches Chromium."""
    request = route.request
    if not allowed(request.url) or request.resource_type in {"image", "media", "font"}:
        route.abort()
        return
    response = route.fetch(max_redirects=0, timeout=12_000)
    if 300 <= response.status < 400 or not allowed(response.url):
        route.abort()
        return
    declared = response.headers.get("content-length")
    if declared and (not declared.isdecimal() or int(declared) > MAX_RESPONSE_BYTES):
        route.abort()
        return
    body = response.body()
    if len(body) > MAX_RESPONSE_BYTES:
        route.abort()
        return
    route.fulfill(response=response, body=body)


def scrape(today: date) -> list[dict]:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    items: dict[str, dict] = {}
    with sync_playwright() as playwright:
        # The container supplies the process boundary; this host's AppArmor
        # policy blocks Chromium's nested user namespace sandbox.
        browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        try:
            context = browser.new_context(accept_downloads=False, service_workers="block")
            context.set_default_timeout(12_000)
            context.set_default_navigation_timeout(20_000)

            context.route("**/*", lambda route: guard_route(route))
            context.route_web_socket("**/*", lambda socket: socket.close())
            page = context.new_page()
            page.goto(PUBLIC_URL, wait_until="domcontentloaded", timeout=20_000)
            page.locator("tr.z-listitem").first.wait_for(timeout=12_000)
            for day in business_days(today):
                page.get_by_placeholder("dd/mm/aaaa").first.fill(day.strftime("%d/%m/%Y"))
                try:
                    with page.expect_response(lambda response: "/bop/zkau" in response.url and response.request.method == "POST", timeout=12_000):
                        page.locator('a[title="Buscar registros con los parámetros indicados"]').click()
                except PlaywrightTimeout as exc:
                    raise RuntimeError(f"La búsqueda del BOP no respondió para {day.isoformat()}") from exc
                # ZK can acknowledge the request before replacing yesterday's rows.
                try:
                    page.wait_for_function(
                        "expected => { const rows = [...document.querySelectorAll('tr.z-listitem')]; "
                        "return rows.length === 0 || rows.every(row => row.querySelectorAll('td')[1]?.innerText.trim() === expected); }",
                        arg=day.strftime("%d/%m/%Y"), timeout=6_000,
                    )
                except PlaywrightTimeout as exc:
                    raise RuntimeError(f"El sumario conserva filas de otra fecha: {day.isoformat()}") from exc
                rows = page.locator("tr.z-listitem").evaluate_all(
                    "rows => rows.map(row => [...row.querySelectorAll('td')].map(cell => cell.innerText.trim()))"
                )
                if len(rows) > MAX_ROWS:
                    raise RuntimeError("Demasiadas filas en el sumario")
                for cells in rows:
                    item = parse_row(cells, day)
                    if item:
                        items[item["url"]] = item
                    if len(items) >= MAX_ITEMS:
                        break
                if len(items) >= MAX_ITEMS:
                    break
            context.close()
        finally:
            browser.close()
    return list(items.values())


def write_atomic(items: list[dict], output: Path = OUTPUT) -> None:
    payload = {"schema": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "items": items[:MAX_ITEMS]}
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("El JSON supera el límite")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    with temp.open("wb") as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temp, output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Consulta y termina")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--today", type=date.fromisoformat, help="Fecha local para una prueba puntual")
    args = parser.parse_args()
    while True:
        day = args.today or datetime.now(ZoneInfo("Europe/Madrid")).date()
        try:
            items = scrape(day)
            write_atomic(items, args.output)
            print(json.dumps({"date": day.isoformat(), "items": len(items), "output": str(args.output)}), flush=True)
        except Exception as exc:
            print(json.dumps({"error": str(exc), "date": day.isoformat()}), flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(60 * 60)


if __name__ == "__main__":
    raise SystemExit(main())
