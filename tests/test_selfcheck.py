import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from tests import synthetic_person

from slice import bitmap, knowledge, rest, selfcheck


def _post(port, path, body):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    c.request("POST", path, body=body)
    r = c.getresponse()
    data = r.read()
    c.close()
    return r.status, data


class TestSelfCheck(unittest.TestCase):
    def test_synth_person_passes_or_warns(self):
        raw = bitmap.encode_png(synthetic_person())
        r = selfcheck.run(raw)
        self.assertIn(r["verdict"], ("pass", "warn"))
        for layer in ("imgqual", "human", "evid", "limbcov", "fit",
                      "stability", "contrad", "gate"):
            self.assertIn(layer, r["layers"], layer)
            self.assertIn(layer, r["severity"], layer)
        self.assertIn("skeleton", r["doc"])

    def test_blank_image_fails_via_detection(self):
        bmp = bitmap.Bitmap.new(60, 60, (255, 255, 255, 255))
        r = selfcheck.run(bitmap.encode_png(bmp))
        self.assertEqual(r["verdict"], "fail")
        self.assertIn("detection:no_person", r["reasons"])
        # unmeasurable layers do not fake a verdict
        self.assertNotIn("evid", r["layers"])

    def test_robust_profile_runs(self):
        raw = bitmap.encode_png(synthetic_person())
        r = selfcheck.run(raw, robust=True)
        self.assertEqual(r["doc"]["engine"]["profile"], "robust")
        self.assertIn(r["verdict"], ("pass", "warn", "fail"))


class TestAuditRest(unittest.TestCase):
    def test_post_audit_endpoint(self):
        rest.Handler.store = knowledge.KnowledgeStore(
            tempfile.mkdtemp())
        rest.Handler.token = None
        srv = ThreadingHTTPServer(("127.0.0.1", 0), rest.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        port = srv.server_address[1]
        try:
            raw = bitmap.encode_png(synthetic_person())
            status, data = _post(port, "/audit", raw)
            self.assertEqual(status, 200)
            body = json.loads(data)
            self.assertIn(body["verdict"], ("pass", "warn"))
            self.assertIn("layers", body)
            self.assertIn("doc", body)
            status, data = _post(port, "/audit?robust=1", raw)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(data)["doc"]["engine"]
                             ["profile"], "robust")
        finally:
            srv.shutdown()


if __name__ == "__main__":
    unittest.main()
