"""MiniWoB++ 本地 HTTP 服务，将 miniwob/html/ 暴露给 Android WebView 访问。

用法:
    python server.py [html_dir] [--port PORT]

html_dir 默认为 /app/html（Docker 容器内路径）。
本地开发可指定 miniwob-plusplus/miniwob/html/ 的实际路径：
    python server.py /path/to/miniwob-plusplus/miniwob/html
"""
import functools
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class CORSRequestHandler(SimpleHTTPRequestHandler):
    """添加 CORS 响应头，支持 Android WebView 跨域请求。"""

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS, HEAD")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # 只打印非 200 请求，减少噪音
        if args and str(args[1]) != "200":
            super().log_message(format, *args)


def main():
    html_dir = sys.argv[1] if len(sys.argv) > 1 else "/app/html"
    port = int(os.environ.get("PORT", 8080))

    if not os.path.isdir(html_dir):
        print(f"ERROR: html_dir '{html_dir}' does not exist", file=sys.stderr)
        print("  For Docker: html/ is copied to /app/html at build time.", file=sys.stderr)
        print("  For local dev: python server.py /path/to/miniwob-plusplus/miniwob/html", file=sys.stderr)
        sys.exit(1)

    handler = functools.partial(CORSRequestHandler, directory=html_dir)
    with ThreadingHTTPServer(("0.0.0.0", port), handler) as httpd:
        print(f"✓ MiniWoB++ server running:")
        print(f"  http://0.0.0.0:{port}/miniwob/click-button.html")
        print(f"  Serving from: {html_dir}")
        print(f"  Android emulator URL: http://10.0.2.2:{port}/miniwob/click-button.html")
        print("  Press Ctrl+C to stop.")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
