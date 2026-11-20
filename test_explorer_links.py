import http.client
from pathlib import Path
import tempfile
import threading
import unittest

from explorer_links import serve


class RevealTest(unittest.TestCase):
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
                    self.assertEqual(status, 200)
                    self.assertIn(b"You can close this tab.", body)
                    self.assertEqual(request("POST", report, Origin=f"http://127.0.0.1:{port}")[0], 200)
                    self.assertEqual(opened, files)
                    files[0].unlink()
                    self.assertEqual(request("GET", model, **nav), (410, b"The file has been moved or deleted."))
                    self.assertEqual(opened, files)
                finally:
                    server.shutdown()
                    thread.join()


if __name__ == "__main__":
    unittest.main()
