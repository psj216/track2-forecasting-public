"""## Executive summary (read this first)
Synthetic House and authenticated proxy services on an internal Docker network only.
No vendor call, secret, dataset fetch or production model is used.
"""

import argparse
import http.client
import json
import select
import socket
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from backtesting.moonshot15.runtime.synthetic import reply
from moonshot15_engine.engine import PROMPTS


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def send_bytes(self, status, raw):
        self.send_response(status)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_CONNECT(self):
        if (
            self.server.mode != "proxy"
            or self.headers.get("Proxy-Authorization")
            != "Basic c3ludGhldGljLXVzZXI6c3ludGhldGljLXBhc3M="
        ):
            self.send_bytes(407, b"{}")
            return
        if self.path != "m16-house:8443":
            self.send_bytes(403, b"{}")
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.flush()
        with socket.create_connection(("m16-house", 8443), timeout=5) as peer:
            streams = [self.connection, peer]
            while True:
                readable, _, _ = select.select(streams, [], [], 5)
                if not readable:
                    return
                for stream in readable:
                    try:
                        data = stream.recv(65536)
                        if not data:
                            return
                        (peer if stream is self.connection else self.connection).sendall(data)
                    except OSError:
                        return

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.server.mode == "proxy":
            if (
                self.headers.get("Proxy-Authorization")
                != "Basic c3ludGhldGljLXVzZXI6c3ludGhldGljLXBhc3M="
            ):
                self.send_bytes(407, b"{}")
                return
            target = urlsplit(self.path)
            if (
                target.hostname != "m16-house"
                or target.port != 8080
                or target.path != "/v1/chat/completions"
            ):
                self.send_bytes(403, b"{}")
                return
            conn = http.client.HTTPConnection("m16-house", 8080, timeout=10)
            try:
                conn.request(
                    "POST",
                    target.path,
                    raw,
                    {
                        "Content-Type": "application/json",
                        "Authorization": self.headers.get("Authorization", ""),
                    },
                )
                response = conn.getresponse()
                self.send_bytes(response.status, response.read())
            finally:
                conn.close()
            return
        if (
            self.path != "/v1/chat/completions"
            or self.headers.get("Authorization") != "Bearer synthetic-house-token"
        ):
            self.send_bytes(401, b"{}")
            return
        if "Proxy-Authorization" in self.headers:
            self.send_bytes(403, b"{}")
            return
        payload = json.loads(raw)
        assert payload["model"] == "synthetic-model"
        assert payload["max_tokens"] == 4000 and payload["temperature"] == 0
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}
        prompt = payload["messages"][0]["content"]
        prefix, context = prompt.split("\nCONTEXT_JSON\n", 1)
        kind = next(k for k, p in PROMPTS.items() if p == prefix)
        context = json.loads(context)
        case = Path("/state/case.txt").read_text().strip()
        if case == "http_error":
            self.send_bytes(503, b"{}")
            return
        content = json.dumps(reply(kind, context))
        if case == "malformed":
            content = "synthetic non-JSON response"
        result = {"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
        self.send_bytes(200, json.dumps(result).encode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["proxy", "house", "tls"])
    args = ap.parse_args()
    port = 8443 if args.mode == "tls" else 8080
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.mode = "house" if args.mode == "tls" else args.mode
    if args.mode == "tls":
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain("/state/cert.pem", "/state/key.pem")
        server.socket = context.wrap_socket(server.socket, server_side=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
