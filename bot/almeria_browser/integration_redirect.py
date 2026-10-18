"""Offline browser regression: an allowed 302 must not reach its off-origin target."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse
import unittest

from playwright.sync_api import sync_playwright, Error as PlaywrightError

from collector import guard_route


class RedirectTests(unittest.TestCase):
    def test_allowed_302_does_not_reach_other_origin(self):
        hits = {"source": 0, "destination": 0}

        class Destination(BaseHTTPRequestHandler):
            def do_GET(self):
                hits["destination"] += 1
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"reached")

            def log_message(self, *_args):
                pass

        destination = ThreadingHTTPServer(("127.0.0.1", 0), Destination)

        class Source(BaseHTTPRequestHandler):
            def do_GET(self):
                hits["source"] += 1
                self.send_response(302)
                self.send_header("Location", f"http://localhost:{destination.server_port}/off-origin")
                self.end_headers()

            def log_message(self, *_args):
                pass

        source = ThreadingHTTPServer(("127.0.0.1", 0), Source)
        threads = [Thread(target=server.serve_forever, daemon=True) for server in (source, destination)]
        for thread in threads:
            thread.start()
        try:
            origin = f"http://127.0.0.1:{source.server_port}/bop/publico.zul"

            def source_only(url):
                parsed = urlparse(url)
                return parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port == source.server_port

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    context = browser.new_context(service_workers="block")
                    context.route("**/*", lambda route: guard_route(route, source_only))
                    page = context.new_page()
                    with self.assertRaises(PlaywrightError):
                        page.goto(origin, wait_until="domcontentloaded", timeout=5_000)
                    context.close()
                finally:
                    browser.close()
            self.assertEqual(hits, {"source": 1, "destination": 0})
        finally:
            for server in (source, destination):
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
