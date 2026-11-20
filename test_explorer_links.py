import http.client
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import explorer_direct

from explorer_links import serve


class RevealTest(unittest.TestCase):
    def test_direct_links_are_private_expiring_selections(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"XDG_STATE_HOME": temp}):
            files = [Path(temp, "sample α.txt"), Path(temp, "report.html")]
            for path in files:
                path.touch()
            urls = explorer_direct.register(files, 1)
            with patch.object(explorer_direct, "reveal") as reveal:
                for url, path in zip(urls, files):
                    explorer_direct.open_direct(url)
                    reveal.assert_called_with(path)
                for bad in (urls[0] + "?extra=1", urls[0].replace(".localhost", ".example"),
                            explorer_direct.PREFIX + "x" * 32):
                    with self.assertRaises(ValueError):
                        explorer_direct.open_direct(bad)
                files[1].unlink()
                with self.assertRaisesRegex(ValueError, "moved"):
                    explorer_direct.open_direct(urls[1])
                with patch("explorer_direct.time.time", return_value=10**11):
                    with self.assertRaisesRegex(ValueError, "expired"):
                        explorer_direct.open_direct(urls[0])
                self.assertEqual(reveal.call_count, 2)

    def test_ordinary_invocation_recognizes_the_installed_fallback(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"BROWSER": ""}):
            opener = Path(tmp, "codex-explorer-open")
            opener.touch()
            fallback = Path(tmp, "x-www-browser")
            # Use a hard link so this check also works without Windows symlink privileges.
            os.link(opener, fallback)
            commands = {"wslpath": "/usr/bin/wslpath", "x-www-browser": str(fallback),
                        "codex-explorer-open": str(opener)}
            with patch("explorer_direct.shutil.which", side_effect=commands.get):
                if os.name == "posix":
                    self.assertTrue(explorer_direct.direct_opener_configured())
                    with patch.dict(os.environ, {"BROWSER": "another-browser"}):
                        self.assertFalse(explorer_direct.direct_opener_configured())
                else:
                    self.assertFalse(explorer_direct.direct_opener_configured())

    def test_other_web_links_use_the_existing_opener(self):
        url = "https://example.com/a?b=c&d=e"
        with patch("sys.argv", ["codex-explorer-open", url]), patch("explorer_direct.os.name", "posix"), patch("os.execvpe") as launch:
            explorer_direct.main()
        self.assertEqual(launch.call_args.args[:2], ("xdg-open", ["xdg-open", url]))
        self.assertEqual(launch.call_args.args[2]["CODEX_EXPLORER_DELEGATING"], "1")

    def test_only_explicit_navigation_reveals_a_registered_file(self):
        with tempfile.TemporaryDirectory() as temp:
            files = [Path(temp, name) for name in ("model α, 1.3mf", "report & preview.html")]
            for path in files:
                path.write_bytes(b"private contents")
            opened = []
            with serve(files, opened.append) as server:
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                try:
                    port = server.server_port
                    model, report = server.targets
                    def request(method, endpoint, **headers):
                        client = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                        try:
                            client.request(method, endpoint, headers=headers)
                            result = client.getresponse()
                            body = result.read()
                            self.assertNotIn(b"private contents", body)
                            return result.status, body
                        finally:
                            client.close()
                    nav = {"Sec-Fetch-User": "?1", "Sec-Fetch-Site": "none",
                           "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"}
                    self.assertEqual(request("HEAD", model, **nav), (200, b""))
                    landing = request("GET", model)[1]
                    self.assertIn(b'lang="en"', landing)
                    self.assertIn(b"<button>Show in File Explorer</button>", landing)
                    self.assertIn(b"<button>", request("GET", report, **nav, Purpose="prefetch")[1])
                    self.assertIn(b"<button>", request("GET", report, **(nav | {"Sec-Fetch-Site": "cross-site"}))[1])
                    self.assertEqual(request("GET", model, Host="foreign.example")[0], 403)
                    self.assertEqual(request("GET", "/unknown", **nav)[0], 404)
                    self.assertEqual(request("POST", model, Origin="https://foreign.example")[0], 403)
                    self.assertEqual(opened, [])
                    status, body = request("GET", model, **nav)
                    self.assertEqual((status, body), (204, b""))
                    self.assertEqual(request("POST", report, Origin=f"http://127.0.0.1:{port}")[0], 204)
                    self.assertEqual(opened, files)
                    files[0].unlink()
                    self.assertEqual(request("GET", model, **nav), (410, b"The file has been moved or deleted."))
                    self.assertEqual(opened, files)
                finally:
                    server.shutdown()
                    thread.join()


if __name__ == "__main__":
    unittest.main()
