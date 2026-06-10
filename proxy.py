#!/usr/bin/env python3
"""
LiveTrack360 CORSプロキシサーバー
使い方: python3 proxy.py
ポート8766で起動します。AR Trackerのプロキシ欄に http://localhost:8766/ を入力してください。

lb.flymaster.net へのリクエストに CORS ヘッダーを付加します。
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.parse import unquote
from urllib.error import HTTPError, URLError
import json, sys

PORT = 8766

HEADERS = {
    'Referer':    'https://livetrack360.com',
    'Origin':     'https://livetrack360.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept':     'application/json, */*',
}

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default logging

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        target = unquote(self.path.lstrip('/'))
        if not target.startswith('http'):
            self._json(400, {'error': 'full URL required as path'})
            return

        print(f"  -> {target}", flush=True)
        try:
            req = Request(target, headers=HEADERS)
            with urlopen(req, timeout=10) as r:
                data = r.read()
                ct = r.headers.get('Content-Type', 'application/json')
            print(f"     200 ({len(data)} bytes)", flush=True)
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self._cors()
            self.end_headers()
            self.wfile.write(data)

        except HTTPError as e:
            body = e.read()
            print(f"     HTTP {e.code}: {body[:80]}", flush=True)
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(body if not body.startswith(b'<') else
                json.dumps({'error': f'HTTP {e.code}'}).encode())

        except URLError as e:
            print(f"     URLError: {e}", flush=True)
            self._json(502, {'error': str(e)})

        except Exception as e:
            print(f"     Error: {e}", flush=True)
            self._json(500, {'error': str(e)})

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')

if __name__ == '__main__':
    httpd = HTTPServer(('localhost', PORT), ProxyHandler)
    print(f"🌐 LT360プロキシ起動中: http://localhost:{PORT}/")
    print(f"   AR Trackerのプロキシ欄に http://localhost:{PORT}/ を入力してください")
    print(f"   終了: Ctrl+C\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
        sys.exit(0)
