import unittest
from datetime import date
import json
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

import bot


BOE = b'''<response><status><code>200</code></status><data><sumario><metadatos><fecha_publicacion>20261016</fecha_publicacion></metadatos><diario><seccion codigo="2B"><departamento><epigrafe>
<item><identificador>BOE-A-2026-1</identificador><titulo>Resolucion de la Diputacion de Granada para proveer dos plazas</titulo><url_html>https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-1</url_html></item>
<item><identificador>BOE-A-2026-2</identificador><titulo>Resolucion del Ayuntamiento de Cordoba para proveer dos plazas</titulo><url_html>https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-2</url_html></item>
<item><identificador>BOE-A-2026-3</identificador><titulo>Granada para proveer dos plazas</titulo><url_html>javascript:alert(1)</url_html></item>
</epigrafe></departamento></seccion></diario></sumario></data></response>'''

RSS = b'''<rss><channel>
<item><title>Bolsa de trabajo Granada</title><link>https://facusoandalucia.es/bolsa-granada/</link><pubDate>Fri, 16 Oct 2026 15:00:00 +0200</pubDate><description>Una bolsa disponible. Consulta la fuente oficial.</description></item>
<item><title>Bolsa de trabajo Malaga</title><link>https://facusoandalucia.es/bolsa-malaga/</link><pubDate>Fri, 16 Oct 2026 15:00:00 +0200</pubDate></item>
<item><title>Granada plazas</title><link>http://127.0.0.1/admin</link><pubDate>Fri, 16 Oct 2026 15:00:00 +0200</pubDate></item>
</channel></rss>'''


class FakeWP:
    def __init__(self):
        self.posts = []

    def categories(self):
        return {slug: i for i, slug in enumerate([
            "granada", "cadiz", "cordoba", "administracion-local", "empleo-publico",
            "oposiciones", "bolsas-de-trabajo", "ofertas-de-empleo-publico", "accion-sindical",
            "administracion-autonomica", "universidades", "administracion-general-del-estado", "sanidad",
            "igualdad"], 1)}

    def existing_records(self, province_id):
        return {(p["meta"]["facuso_source_url"], bot.text_only(p["title"]))
                for p in self.posts if province_id in p["categories"]}

    def slug_exists(self, slug):
        return any(p["slug"] == slug for p in self.posts)

    def request(self, endpoint, *, payload=None):
        self.posts.append(payload)


class BotTests(unittest.TestCase):
    def test_boe_filters_by_exact_province_and_official_url(self):
        rows = bot.parse_boe(BOE, province="Granada", published=date(2026, 10, 16))
        self.assertEqual([row["url"] for row in rows], ["https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-1"])
        self.assertEqual(rows[0]["date"], "2026-10-16")

    def test_boe_rejects_wrong_date_and_dtd(self):
        with self.assertRaises(bot.BotError):
            bot.parse_boe(BOE, province="Granada", published=date(2026, 10, 15))
        with self.assertRaises(bot.BotError):
            bot.parse_boe(b"<!DOCTYPE a>" + BOE, province="Granada", published=date(2026, 10, 16))

    def test_rss_skips_other_province_and_bad_link(self):
        rows = bot.parse_rss(RSS, province="Granada", source="fac", allowed_hosts={"facusoandalucia.es"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["date"], "2026-10-16")
        self.assertEqual(rows[0]["excerpt"], "")

    def test_escaped_markup_in_title_stays_text(self):
        raw = b'<rss><channel><item><title>&amp;lt;img src=x&amp;gt; Granada bolsa de trabajo</title><link>https://facusoandalucia.es/bolsa/</link><pubDate>Fri, 16 Oct 2026 15:00:00 +0200</pubDate></item></channel></rss>'
        item = bot.parse_rss(raw, province="Granada", source="fac", allowed_hosts={"facusoandalucia.es"})[0]
        payload = bot.post_payload(item, "granada", FakeWP().categories(), "draft")
        self.assertNotIn("<img", payload["title"])
        self.assertIn("&lt;img", payload["title"])

    def test_url_validation_and_redirect_block(self):
        for url in ("http://evil.example/x", "https://facusoandalucia.es.evil.example/x",
                    "https://facusoandalucia.es@evil.example/x", "javascript:alert(1)"):
            with self.assertRaises(bot.BotError):
                bot.canonical_url(url, {"facusoandalucia.es"})
        handler = bot.RestrictedRedirect({"facusoandalucia.es"})
        with self.assertRaises(bot.BotError):
            handler.redirect_request(None, None, 302, "redirect", {}, "https://evil.example/inside")
        with self.assertRaises(bot.BotError):
            bot.canonical_url("http://wordpress/wp-json/wp/v2/posts", {"wordpress"}, local=True)
        self.assertEqual(bot.canonical_url("http://facuso-importacion-wordpress-1/wp-json/wp/v2/posts",
                                           {"facuso-importacion-wordpress-1"}, local=True),
                         "http://facuso-importacion-wordpress-1/wp-json/wp/v2/posts")

    def test_dry_run_never_posts_and_rerun_deduplicates(self):
        item = bot.parse_rss(RSS, province="Granada", source="fac", allowed_hosts={"facusoandalucia.es"})[0]
        wp = FakeWP()
        self.assertEqual(bot.run("granada", {}, dry_run=True, publish=False, wp=wp, items=[item])["created"], 0)
        self.assertEqual(wp.posts, [])
        self.assertEqual(bot.run("granada", {}, dry_run=False, publish=False, wp=wp, items=[item])["created"], 1)
        self.assertEqual(bot.run("granada", {}, dry_run=False, publish=False, wp=wp, items=[item])["existing"], 1)
        self.assertEqual(wp.posts[0]["status"], "draft")
        self.assertEqual((wp.posts[0]["comment_status"], wp.posts[0]["ping_status"]), ("closed", "closed"))
        self.assertEqual(wp.posts[0]["date"], "2026-10-16T12:00:00")

    def test_shared_item_separate_province_posts(self):
        item = {"title": "Bolsa de trabajo Cádiz y Granada", "url": "https://facusoandalucia.es/bolsa-compartida/",
                "date": "2026-10-16", "excerpt": "", "source": "fac"}
        wp = FakeWP()
        self.assertEqual(bot.run("granada", {}, dry_run=False, publish=False, wp=wp, items=[item])["created"], 1)
        self.assertEqual(bot.run("cadiz", {}, dry_run=False, publish=False, wp=wp, items=[item])["created"], 1)
        self.assertNotEqual(wp.posts[0]["slug"], wp.posts[1]["slug"])
        self.assertEqual(wp.posts[0]["categories"], [1, 5, 7])
        self.assertEqual(wp.posts[1]["categories"], [2, 5, 7])

    def test_cadiz_two_notices_same_pdf_page_are_distinct(self):
        base = {"url": "https://www.bopcadiz.es/export/sites/default/.boletines_pdf/2026/10_octubre/BOP200_16-10-26.pdf#page=4",
                "date": "2026-10-16", "excerpt": "", "source": "bop"}
        first = {**base, "title": "332.720.- Convocatoria de varias plazas"}
        second = {**base, "title": "332.721.- Convocatoria de una plaza"}
        wp = FakeWP()
        result = bot.run("cadiz", {}, dry_run=False, publish=False, wp=wp, items=[first, second])
        self.assertEqual(result["created"], 2)
        self.assertNotEqual(wp.posts[0]["slug"], wp.posts[1]["slug"])
        self.assertEqual(bot.run("cadiz", {}, dry_run=False, publish=False, wp=wp, items=[first, second])["created"], 0)

    def test_almeria_browser_file_rejects_foreign_and_old_links(self):
        today = date.today()
        payload = {"schema": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "items": [
            {"title": "Convocatoria de una plaza de técnico", "url": "https://app.dipalme.org/bop/services/manager/edicto/2026/2792/anuncio.pdf", "date": today.isoformat(), "excerpt": "", "source": "bop"},
            {"title": "Convocatoria de una plaza de técnico", "url": "https://evil.example/file.pdf", "date": today.isoformat(), "excerpt": "", "source": "bop"},
            {"title": "Convocatoria de una plaza de técnico", "url": "https://app.dipalme.org/bop/services/manager/edicto/2026/2793/anuncio.pdf", "date": "2020-01-01", "excerpt": "", "source": "bop"}
        ]}
        with TemporaryDirectory() as directory:
            path = Path(directory) / "bop.json"
            path.write_text(json.dumps(payload))
            rows = bot.read_almeria_browser_file(str(path), today=today)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source"], "bop")
            path.unlink()
            path.symlink_to("/etc/passwd")
            with self.assertRaises(bot.BotError):
                bot.read_almeria_browser_file(str(path), today=today)

    def test_sector_requires_explicit_issuer(self):
        university = {"title": "Resolución de la Universidad de Cádiz para proveer plazas", "source": "boe"}
        municipality = {"title": "Resolución del Ayuntamiento de Granada para proveer plazas", "source": "boe"}
        unknown = {"title": "Convocatoria para proveer una plaza", "source": "bop"}
        self.assertIn("universidades", bot.category_slugs(university, "cadiz"))
        self.assertNotIn("administracion-local", bot.category_slugs(university, "cadiz"))
        self.assertIn("administracion-local", bot.category_slugs(municipality, "granada"))
        self.assertNotIn("administracion-local", bot.category_slugs(unknown, "granada"))

    def test_boe_detail_uses_only_official_paragraphs(self):
        html = b'''<html><p>Outside</p><div id="textoxslt"><p class="parrafo">Bases de la convocatoria.</p><script>bad()</script><p class="parrafo_2">Dos plazas de Administrativo.</p></div><p>Footer</p><span>BOE-A-2026-21369</span></html>'''
        self.assertEqual(bot.parse_boe_detail(html, identifier="BOE-A-2026-21369"),
                         ["Bases de la convocatoria.", "Dos plazas de Administrativo."])

    def test_cycle_deadline_cannot_be_swallowed_by_boe_fallback(self):
        item = {"title": "Plaza en Granada", "url": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-12345",
                "date": "2026-10-16", "excerpt": "", "source": "boe"}
        with patch.object(bot, "fetch", side_effect=bot.CycleDeadline("deadline")):
            with self.assertRaises(bot.CycleDeadline):
                bot.enrich_boe(item)

    def test_enrich_existing_updates_only_generated_own_post(self):
        item = {"title": "Resolución de la Universidad de Cádiz para proveer plazas",
                "url": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-12345",
                "date": "2026-10-16", "excerpt": "", "source": "boe"}
        categories = FakeWP().categories()
        original = bot.post_payload(item, "cadiz", categories, "publish")
        row = {"id": 123, "slug": original["slug"], "status": "publish",
               "comment_status": "closed", "ping_status": "closed",
               "title": {"raw": item["title"]}, "meta": original["meta"],
               "content": {"raw": original["content"]},
               "categories": [categories["cadiz"], categories["administracion-local"],
                              categories["empleo-publico"], categories["oposiciones"]]}
        edited = {**row, "id": 124, "content": {"raw": original["content"] + "<p>Nota redactada a mano.</p>"}}
        recategorized = {**row, "id": 125, "categories": [*row["categories"], categories["igualdad"]]}

        class ExistingWP:
            def __init__(self):
                self.updates = []

            def categories(self):
                return categories

            def own_posts(self):
                return [row, edited, recategorized]

            def request(self, endpoint, *, payload=None):
                self.updates.append((endpoint, payload))

        wp = ExistingWP()
        with patch.object(bot, "enrich_boe", side_effect=lambda x: {**x, "boe_paragraphs": ["Dos plazas de Administrativo."]}):
            outcome = bot.enrich_existing("cadiz", wp)
        self.assertEqual((outcome["updated"], outcome["manual_skipped"], outcome["protected_categories"]), (2, 1, 1))
        self.assertEqual(len(wp.updates), 2)
        self.assertEqual(wp.updates[0][0], "/posts/123")
        self.assertIn("Dos plazas de Administrativo.", wp.updates[0][1]["content"])
        self.assertIn(categories["universidades"], wp.updates[0][1]["categories"])
        self.assertIn(categories["igualdad"], wp.updates[1][1]["categories"])
        self.assertIn(categories["administracion-local"], wp.updates[1][1]["categories"])
        self.assertEqual((wp.updates[0][1]["comment_status"], wp.updates[0][1]["ping_status"]),
                         ("closed", "closed"))

    def test_enrich_existing_closes_manual_post_without_replacing_text(self):
        item = {"title": "Resolución del Ayuntamiento de Granada para proveer plazas",
                "url": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-22222",
                "date": "2026-10-16", "excerpt": "", "source": "boe"}
        categories = FakeWP().categories()
        original = bot.post_payload(item, "granada", categories, "publish")
        row = {"id": 222, "slug": original["slug"], "status": "publish", "title": {"raw": item["title"]},
               "meta": original["meta"], "content": {"raw": original["content"] + "<p>Nota propia.</p>"},
               "categories": original["categories"], "comment_status": "open", "ping_status": "open"}

        class ExistingWP:
            def __init__(self):
                self.payload = None

            def categories(self):
                return categories

            def own_posts(self):
                return [row]

            def request(self, endpoint, *, payload=None):
                self.payload = payload

        wp = ExistingWP()
        outcome = bot.enrich_existing("granada", wp)
        self.assertEqual((outcome["updated"], outcome["closed_only"]), (0, 1))
        self.assertEqual(wp.payload["categories"], row["categories"])
        self.assertNotIn("content", wp.payload)

    def test_bop_filters_nonemployment_and_keeps_original_link(self):
        data = '''<html><title>BOP - 16/10/2026</title><li class="elementoListado"><a href="/publica/buscador-anuncios/anuncio/p1/" class="enlace_elemento">Ir</a><h3 class="titulo_elemento">Oferta de empleo público 2026</h3><div>16/10/2026</div></li><li class="elementoListado"><a href="/publica/buscador-anuncios/anuncio/p2/" class="enlace_elemento">Ir</a><h3 class="titulo_elemento">Convocatoria de subvenciones 2026</h3></li></html>'''.encode()
        rows = bot.parse_bop_html(data, province_slug="granada", published=date(2026, 10, 16))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://bop.dipgra.es/publica/buscador-anuncios/anuncio/p1/")


if __name__ == "__main__":
    unittest.main()
