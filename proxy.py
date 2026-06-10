#!/usr/bin/env python3
"""
LiveTrack360 CORSプロキシサーバー
使い方: python3 proxy.py
ポート8766で起動します。AR Trackerのプロキシ欄に http://localhost:8766/ を入力してください。
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.parse import unquote
from urllib.error import URLError
import sys

PORT = 8766

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {args[0]} {args[1]}", flush=True)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        target = unquote(self.path.lstrip('/'))
        if not target.startswith('http'):
            self.send_response(400); self.end_headers()
            self.wfile.write(b'Bad Request: URL required')
            return
        print(f"  Proxying: {target}", flush=True)
        try:
            req = Request(target, headers={
                'Referer': 'https://livetrack360.com',
                'Origin':  'https://livetrack360.com',
                'User-Agent': 'Mozilla/5.0',
            })
            with urlopen(req, timeout=10) as r:
                data = r.read()
            self.send_response(200)
            self.send_header('Content-Type', r.headers.get('Content-Type', 'application/json'))
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        except URLError as e:
            self.send_response(502)
            self._cors()
            self.end_headers()
            self.wfile.write(str(e).encode())

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
