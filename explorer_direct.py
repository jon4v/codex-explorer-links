"""Expiring local selections for WSL openers. Direct links never need a web server."""
import contextlib
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import sys
import time
from urllib.parse import urlsplit

from explorer_desktop import reveal


# Browsers block port zero. The fragment never enters an HTTP request target.
PREFIX = "http://127.0.0.1:0/#codex-explorer-"
LEGACY_PREFIX = "http://codex-explorer.localhost/"
TOKEN = re.compile(r"[A-Za-z0-9_-]{32}")


@contextlib.contextmanager
def registry():
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    directory = state / "codex-explorer-links"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = directory / "links.sqlite"
    db.touch(mode=0o600, exist_ok=True)
    with contextlib.closing(sqlite3.connect(db)) as conn, conn:
        conn.execute("CREATE TABLE IF NOT EXISTS links (token TEXT PRIMARY KEY, path TEXT NOT NULL, expires INTEGER NOT NULL)")
        conn.execute("DELETE FROM links WHERE expires <= ?", (int(time.time()),))
        yield conn


def register(paths, hours):
    urls = []
    expires = int(time.time()) + hours * 3600
    with registry() as conn:
        for path in paths:
            token = secrets.token_urlsafe(24)
            conn.execute("INSERT INTO links VALUES (?, ?, ?)", (token, str(path), expires))
            urls.append(PREFIX + token)
    return urls


def open_direct(url):
    prefix = LEGACY_PREFIX if url.startswith(LEGACY_PREFIX) else PREFIX
    token = url.removeprefix(prefix)
    if not url.startswith(prefix) or not TOKEN.fullmatch(token):
        raise ValueError("Invalid File Explorer link.")
    with registry() as conn:
        row = conn.execute("SELECT path FROM links WHERE token = ?", (token,)).fetchone()
    if not row:
        raise ValueError("This link has expired or was created by a different user.")
    path = Path(row[0])
    if not path.is_file():
        raise ValueError("The file has been moved or deleted.")
    reveal(path)


def direct_opener_configured():
    if os.name != "posix" or not shutil.which("wslpath"):
        return False
    browser = os.environ.get("BROWSER", "").split(":", 1)[0].split()
    if browser and Path(browser[0]).name == "codex-explorer-open":
        return True
    if browser:
        return False
    fallback = shutil.which("x-www-browser")
    opener = shutil.which("codex-explorer-open")
    return bool(fallback and opener and os.path.samefile(fallback, opener))


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: codex-explorer-open URL")
    url = sys.argv[1]
    try:
        parsed = urlsplit(url)
        if url.startswith(PREFIX) or parsed.hostname == "codex-explorer.localhost":
            open_direct(url)
        elif parsed.scheme in {"http", "https"} and parsed.hostname and os.name == "posix":
            if os.environ.get("CODEX_EXPLORER_DELEGATING"):
                raise ValueError("Configure an independent xdg-open for ordinary web links.")
            env = dict(os.environ, CODEX_EXPLORER_DELEGATING="1")
            if "codex-explorer-open" in env.get("BROWSER", ""):
                env.pop("BROWSER")
            os.execvpe("xdg-open", ["xdg-open", url], env)
        else:
            raise ValueError("Expected an HTTP or HTTPS URL.")
    except (ValueError, OSError, sqlite3.Error, RuntimeError) as exc:
        sys.exit(str(exc))
