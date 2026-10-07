"""REST error paths: malformed input must get an HTTP status, not a
connection drop or a blank 500."""
import http.client
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from slice import knowledge, rest


def _serve(tmpdir):
    rest.Handler.store = knowledge.KnowledgeStore(tmpdir)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), rest.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def _get(port, path):
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}{path}") as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


class TestRestErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.httpd, cls.port = _serve(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls._tmp.cleanup()

    def test_corrupt_doc_returns_500_with_body(self):
        # a doc file that exists but is not JSON must not blank the
        # connection — report, don't crash
        kid = "k_" + "ab" * 6
        with open(os.path.join(self._tmp.name, kid + ".json"),
                  "w") as f:
            f.write("{not json")
        status, body = _get(self.port, f"/knowledge/{kid}")
        self.assertEqual(status, 500)
        self.assertIn("corrupt", body["error"])

    def test_nondict_doc_returns_500_with_body(self):
        kid = "k_" + "cd" * 6
        with open(os.path.join(self._tmp.name, kid + ".json"),
                  "w") as f:
            f.write("[1, 2]")
        status, body = _get(self.port, f"/knowledge/{kid}")
        self.assertEqual(status, 500)
        self.assertIn("corrupt", body["error"])

    def test_bad_content_length_gets_400_not_drop(self):
        # http.client lets us send a malformed Content-Length
        c = http.client.HTTPConnection("127.0.0.1", self.port)
        c.putrequest("POST", "/analyze")
        c.putheader("Content-Length", "abc")
        c.endheaders()
        r = c.getresponse()
        self.assertEqual(r.status, 400)
        c.close()


if __name__ == "__main__":
    unittest.main()
