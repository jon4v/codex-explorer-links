"""Create temporary links that select specified files in Windows Explorer."""
import argparse
import html
import os
from pathlib import Path
import secrets
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from explorer_desktop import powershell, reveal
from explorer_direct import direct_opener_configured, register


class Links(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Keep private link tokens out of request logs.

    def reply(self, status, body=b""):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        if status != 204:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def handle_link(self):
        authority = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != authority:
            return self.reply(403)
        path = self.server.targets.get(self.path)
        if path is None:
            return self.reply(404)
        if not path.is_file():
            return self.reply(410, b"The file has been moved or deleted.")
        if self.command == "HEAD":
            return self.reply(200)
        if self.command == "POST":
            if self.headers.get("Origin") != f"http://{authority}":
                return self.reply(403)
        else:
            # Terminal activation is an explicit, top-level navigation. Plain GETs,
            # previews and links from web pages only display the confirmation button.
            automatic = (
                self.headers.get("Sec-Fetch-User") == "?1"
                and self.headers.get("Sec-Fetch-Site") == "none"
                and self.headers.get("Sec-Fetch-Mode") == "navigate"
                and self.headers.get("Sec-Fetch-Dest") == "document"
                and not self.headers.get("Purpose") and not self.headers.get("Sec-Purpose")
            )
            if not automatic:
                name = html.escape(path.name)
                return self.reply(200, (
                    '<!doctype html><html lang="en"><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<title>Show in File Explorer</title>'
                    f'<h1>{name}</h1><form method="post">'
                    '<button>Show in File Explorer</button></form></html>'
                ).encode())
        try:
            self.server.reveal(path)
        except (OSError, subprocess.SubprocessError, RuntimeError):
            return self.reply(503, b"File Explorer could not confirm the file selection and foreground focus.")
        self.reply(204)

    do_GET = do_HEAD = do_POST = handle_link


def serve(files, opener=reveal):
    server = ThreadingHTTPServer(("127.0.0.1", 0), Links)
    server.targets = {"/" + secrets.token_urlsafe(24): path for path in files}
    server.reveal = opener
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--direct", dest="direct", action="store_true", help="Use the WSL direct opener and exit.")
    mode.add_argument("--browser", dest="direct", action="store_false", help="Serve browser-compatible links.")
    parser.set_defaults(direct=None)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--hours", type=int, choices=range(1, 169), metavar="1..168", default=24)
    args = parser.parse_args()
    paths = list(dict.fromkeys(path.resolve() for path in args.files))
    for path in paths:
        if not path.is_file():
            parser.error(f"File not found: {path}")
    try:
        powershell()
    except (OSError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    direct = direct_opener_configured() if args.direct is None else args.direct
    if direct and os.name == "nt":
        parser.error("Direct links require the WSL opener. Use --browser on native Windows.")
    if direct:
        for path, url in zip(paths, register(paths, args.hours)):
            print(f"{path.name}\t{url}")
        return
    with serve(paths) as server:
        for endpoint, path in server.targets.items():
            print(f"{path.name}\thttp://127.0.0.1:{server.server_port}{endpoint}", flush=True)
        timer = threading.Timer(args.hours * 3600, server.shutdown)
        timer.daemon = True
        timer.start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            timer.cancel()


if __name__ == "__main__":
    main()
