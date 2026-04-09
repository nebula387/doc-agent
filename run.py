"""
Entrypoint for Hugging Face Spaces.
Starts a health check server on port 7860 (required by HF)
and runs the Telegram bot in the same process.
"""
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import bot


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"running")

    def log_message(self, *_):
        pass


def _start_health_server():
    HTTPServer(("", 7860), _HealthHandler).serve_forever()


if __name__ == "__main__":
    threading.Thread(target=_start_health_server, daemon=True).start()
    asyncio.run(bot.main())
