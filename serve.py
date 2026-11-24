#!/usr/bin/env python3
"""Run the page locally: python3 serve.py, then open http://localhost:8000/tools/runway

The page reads three same-origin files. This serves index.html and fetches those three from
birdbrain.wtf, unless a local market.json exists (from `python3 market.py market.json`)."""
import http.server, pathlib, urllib.request

HERE = pathlib.Path(__file__).parent
LIVE = {"/api/treasury", "/tools/ksm-dot/data.json", "/tools/runway/market.json"}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/tools/runway", "/tools/runway/"):
            body, kind = (HERE / "index.html").read_bytes(), "text/html; charset=utf-8"
        elif path == "/tools/runway/market.json" and (HERE / "market.json").exists():
            body, kind = (HERE / "market.json").read_bytes(), "application/json"
        elif path in LIVE:
            req = urllib.request.Request("https://birdbrain.wtf" + path, headers={"User-Agent": "birdbrain-runway-local"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body, kind = r.read(), "application/json"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


print("http://localhost:8000/tools/runway")
http.server.ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()
