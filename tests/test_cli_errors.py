"""CLI error contract: unreadable input exits 2, never a traceback."""
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from slice.__main__ import main


class TestCliErrors(unittest.TestCase):
    def test_missing_file_exits_2_not_traceback(self):
        # exit-code contract: 1 = defect found, 2 = input unloadable —
        # a missing file must not produce an uncaught OSError
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            rc = main(["analyze", "/nonexistent-xyz.png"])
        self.assertEqual(rc, 2)
        self.assertNotIn("Traceback", err.getvalue())

    def test_audit_missing_file_exits_2(self):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            rc = main(["audit", "/nonexistent-xyz.png"])
        self.assertEqual(rc, 2)
        self.assertNotIn("Traceback", err.getvalue())

    def test_corrupt_image_exits_2_not_traceback(self):
        # corrupt bytes inside a valid PNG container must decode to
        # exit 2 (UnsupportedFormat), not an uncaught zlib/IndexError
        import tempfile, os
        with tempfile.NamedTemporaryFile(
                suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
            path = f.name
        try:
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                rc = main(["analyze", path])
            self.assertEqual(rc, 2)
            self.assertNotIn("Traceback", err.getvalue())
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
