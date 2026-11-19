"""Knowledge JSON spec conformance — docs/KNOWLEDGE_JSON.md is the
contract; these tests pin the implementation to it so the spec and
the code cannot drift apart silently.

Covered promises:
- build() documents carry every core block the spec calls required
- pipeline documents validate and carry the documented additions
- unknown extra keys are tolerated (the reader-side promise, kept
  by validate() itself)
- the `slice validate` CLI accepts good documents and rejects bad
  ones with reasons (exit 0 / 1 / 2)
- the spec document names every schema, top-level field, warning
  code and joint the implementation can produce
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from tests import synthetic_person

from slice import __main__, bitmap, knowledge, pipeline
from slice.landmarks import JOINTS
from slice.skeleton import Skeleton

CORE_KEYS = ("schema", "id", "created_at", "engine", "source",
             "skeleton", "pose", "ratio", "prediction", "coverage",
             "export")

WARNING_CODES = ("few_observed_joints", "no_observed_torso",
                 "no_observed_wrists", "no_observed_feet",
                 "no_observed_head", "unknown_body_model")

SPEC_PATH = os.path.join(os.path.dirname(__file__), "..",
                         "docs", "KNOWLEDGE_JSON.md")


def _bare_build_doc():
    """A build()-only document (no pipeline additions)."""
    skel = Skeleton(100, 200)
    return knowledge.build(skel, {}, None,
                           engine={"name": "spec-test",
                                   "version": "0",
                                   "slice": "0"})


def _pipeline_doc():
    raw = bitmap.encode_png(synthetic_person())
    return pipeline.strip_runtime(
        pipeline.analyze(raw, source_name="synth.png"))


def _run_validate_cli(paths):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = __main__.main(["validate"] + list(paths))
    return rc, out.getvalue(), err.getvalue()


def _write(tmp, name, doc):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(doc, str):
            f.write(doc)
        else:
            json.dump(doc, f)
    return path


class TestSpecConformance(unittest.TestCase):
    def test_build_doc_carries_core_blocks(self):
        doc = _bare_build_doc()
        for key in CORE_KEYS:
            self.assertIn(key, doc)
        self.assertEqual(doc["schema"], knowledge.SCHEMA)
        self.assertEqual(knowledge.validate(doc), [])

    def test_source_name_keeps_base_name_only(self):
        # a shared document must not carry the caller's OS user or
        # folder names, whichever separator the path used
        for given in ("/home/hanako/family/beach.png",
                      "C:\\Users\\hanako\\beach.png",
                      "beach.png"):
            doc = knowledge.build(Skeleton(100, 200), {}, None,
                                  source_name=given,
                                  engine={"name": "spec-test"})
            self.assertEqual(doc["source"]["name"], "beach.png")
        self.assertEqual(_bare_build_doc()["source"]["name"], "")

    def test_build_with_analysis_stamps_v11(self):
        skel = Skeleton(100, 200)
        doc = knowledge.build(skel, {}, None,
                              engine={"name": "t", "version": "0",
                                      "slice": "0"},
                              analysis={"angles": {"x": 1.0}})
        self.assertEqual(doc["schema"], knowledge.SCHEMA_V11)
        self.assertEqual(knowledge.validate(doc), [])

    def test_pipeline_doc_validates_with_additions(self):
        doc = _pipeline_doc()
        self.assertEqual(knowledge.validate(doc), [])
        # documented pipeline additions
        self.assertIn("style", doc)
        self.assertIn("warnings", doc)
        self.assertIn("filled", doc["prediction"])
        self.assertIn("analysis", doc)
        self.assertEqual(doc["schema"], knowledge.SCHEMA_V11)

    def test_unknown_keys_tolerated(self):
        # the compatibility promise: field addition must not break
        # readers — validate() is the shipped reader gate
        doc = _pipeline_doc()
        doc["future_block"] = {"anything": 1}
        doc["skeleton"]["future_field"] = [1, 2, 3]
        self.assertEqual(knowledge.validate(doc), [])

    def test_coverage_adds_up(self):
        doc = _pipeline_doc()
        cov = doc["coverage"]
        self.assertEqual(cov["joints_total"], len(JOINTS))
        self.assertEqual(
            cov["observed"] + cov["predicted"] + cov["unfilled"],
            cov["joints_total"])

    def test_export_layout_matches_spec(self):
        doc = _pipeline_doc()
        exp = doc["export"]
        self.assertEqual(exp["keypoint_order"], JOINTS)
        self.assertEqual(len(exp["keypoints_2d"]), 3 * len(JOINTS))
        self.assertEqual(len(exp["keypoints_state"]), len(JOINTS))
        self.assertTrue(set(exp["keypoints_state"])
                        <= {"observed", "predicted", "absent"})


class TestValidateCli(unittest.TestCase):
    def test_valid_file_exit0(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "ok.json", _pipeline_doc())
            rc, out, _ = _run_validate_cli([p])
        self.assertEqual(rc, 0)
        self.assertIn("valid", out)

    def test_analyze_cli_drops_directory_from_source(self):
        raw = bitmap.encode_png(synthetic_person())
        with tempfile.TemporaryDirectory() as tmp:
            img = os.path.join(tmp, "hanako", "beach.png")
            os.makedirs(os.path.dirname(img))
            with open(img, "wb") as f:
                f.write(raw)
            out = os.path.join(tmp, "k.json")
            with redirect_stdout(io.StringIO()), \
                    redirect_stderr(io.StringIO()):
                rc = __main__.main(["analyze", img, "-o", out])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8") as f:
                text = f.read()
        self.assertEqual(json.loads(text)["source"]["name"], "beach.png")
        self.assertNotIn(tmp, text)
        self.assertNotIn("hanako", text)

    def test_invalid_file_exit1_with_reasons(self):
        doc = _pipeline_doc()
        doc["schema"] = "slice.knowledge/v9"
        doc["skeleton"]["joints"]["head"]["confidence"] = 1.5
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "bad.json", doc)
            rc, out, _ = _run_validate_cli([p])
        self.assertEqual(rc, 1)
        self.assertIn("invalid", out)
        self.assertIn("schema must be one of", out)
        self.assertIn("bad confidence", out)

    def test_prediction_falsification_rejected(self):
        # claim a joint as observed in prediction while the
        # skeleton itself says predicted — fill dressed as evidence
        doc = _pipeline_doc()
        name = doc["prediction"]["observed"][0]
        doc["skeleton"]["joints"][name]["state"] = "predicted"
        with tempfile.TemporaryDirectory() as d:
            p = _write(d, "lie.json", doc)
            rc, out, _ = _run_validate_cli([p])
        self.assertEqual(rc, 1)
        self.assertIn(name, out)

    def test_missing_and_malformed_files_exit2(self):
        with tempfile.TemporaryDirectory() as d:
            notjson = _write(d, "x.json", "{not json")
            rc, _, err = _run_validate_cli(
                [os.path.join(d, "nope.json"), notjson])
        self.assertEqual(rc, 2)
        self.assertIn("cannot load", err)

    def test_mixed_batch_reports_each(self):
        with tempfile.TemporaryDirectory() as d:
            good = _write(d, "good.json", _pipeline_doc())
            bad_doc = _pipeline_doc()
            del bad_doc["export"]
            bad = _write(d, "bad.json", bad_doc)
            rc, out, _ = _run_validate_cli([good, bad])
        self.assertEqual(rc, 1)
        self.assertIn("good.json: valid", out)
        self.assertIn("bad.json: invalid", out)
        self.assertIn("missing export", out)


class TestSpecDocument(unittest.TestCase):
    """The spec text must name everything the implementation can
    emit — if a field, code or joint is added in code, this fails
    until the spec is updated."""

    @classmethod
    def setUpClass(cls):
        with open(SPEC_PATH, encoding="utf-8") as f:
            cls.spec = f.read()

    def test_spec_names_schemas_and_core_keys(self):
        for s in knowledge.SCHEMAS:
            self.assertIn(s, self.spec)
        for key in CORE_KEYS + ("style", "warnings", "analysis",
                                "people"):
            self.assertIn("`%s`" % key, self.spec)

    def test_spec_names_every_warning_code(self):
        for code in WARNING_CODES:
            self.assertIn(code, self.spec)
        # and the codes named here are exactly the ones the
        # pipeline can emit
        import inspect
        from slice import pipeline as pl
        src = inspect.getsource(pl._warnings)
        for code in WARNING_CODES[:5]:
            self.assertIn(code, src)
        self.assertIn("unknown_body_model",
                      inspect.getsource(pl._build_doc))

    def test_spec_names_joint_vocabulary(self):
        for name in JOINTS:
            self.assertIn(name, self.spec)


if __name__ == "__main__":
    unittest.main()
