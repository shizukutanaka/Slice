"""Tests for GET /export/<id>.<fmt> — skeleton formats from the store."""
import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from slice import bitmap, knowledge, rest
from tests import synthetic_person


def _serve():
    tmp = tempfile.mkdtemp()
    rest.Handler.store = knowledge.KnowledgeStore(tmp)
    rest.Handler.token = None
    srv = ThreadingHTTPServer(("127.0.0.1", 0), rest.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _post_analyze(port):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    body = bitmap.encode_png(synthetic_person())
    c.request("POST", "/analyze?save=1", body=body,
              headers={"Content-Length": str(len(body))})
    r = c.getresponse()
    doc = json.loads(r.read())
    c.close()
    return doc


def _get(port, path):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    c.request("GET", path)
    r = c.getresponse()
    body = r.read()
    ctype = r.getheader("Content-Type")
    c.close()
    return r.status, ctype, body


class TestRestExport(unittest.TestCase):
    def setUp(self):
        self.srv = _serve()
        self.port = self.srv.server_address[1]
        self.addCleanup(self.srv.shutdown)
        self.doc = _post_analyze(self.port)
        self.kid = self.doc["id"]

    def test_bvh_export(self):
        status, ctype, body = _get(
            self.port, f"/export/{self.kid}.bvh")
        self.assertEqual(status, 200)
        self.assertIn(b"HIERARCHY", body)

    def test_coco_export_json(self):
        status, ctype, body = _get(
            self.port, f"/export/{self.kid}.coco")
        self.assertEqual(status, 200)
        self.assertEqual(ctype, "application/json")
        self.assertGreater(json.loads(body)["num_keypoints"], 10)

    def test_heatmap_is_png(self):
        status, ctype, body = _get(
            self.port, f"/export/{self.kid}.heatmap")
        self.assertEqual(status, 200)
        self.assertEqual(ctype, "image/png")
        self.assertTrue(body.startswith(b"\x89PNG"))

    def test_bad_format_404(self):
        status, _, _ = _get(
            self.port, f"/export/{self.kid}.exe")
        self.assertEqual(status, 404)

    def test_missing_doc_404(self):
        status, _, _ = _get(
            self.port, "/export/k_000000000000.bvh")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
