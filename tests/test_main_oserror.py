"""CLI dispatch — file path mistakes are one-line errors, not tracebacks."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from slice import __main__


def _run(argv):
    err = io.StringIO()
    with redirect_stderr(err), redirect_stdout(io.StringIO()):
        rc = __main__.main(argv)
    return rc, err.getvalue()


class MainOSErrorTest(unittest.TestCase):
    def test_missing_input_file(self):
        with tempfile.TemporaryDirectory() as d:
            missing = os.path.join(d, "nope.png")
            rc, err = _run(["analyze", missing])
        self.assertEqual(rc, 2)
        self.assertIn("nope.png", err)
        self.assertNotIn("Traceback", err)

    def test_directory_as_input(self):
        with tempfile.TemporaryDirectory() as d:
            rc, err = _run(["analyze", d])
        self.assertEqual(rc, 2)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
