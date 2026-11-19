"""Check that the roadmap's published scores match its tables."""
import re
import unittest
from pathlib import Path


PHASES = Path(__file__).resolve().parents[1] / "docs" / "PHASES.md"


class TestPhaseProgress(unittest.TestCase):
    def test_completion_scores_match_status_rows(self):
        text = PHASES.read_text(encoding="utf-8")
        phases = re.split(r"^## Phase (\d+) — (.+)（([^\n]+)）\n",
                          text, flags=re.MULTILINE)[1:]
        self.assertTrue(phases, "No Phase progress tables found")
        complete = total = 0
        for number, title, score, section in zip(
                phases[::4], phases[1::4], phases[2::4], phases[3::4]):
            with self.subTest(phase=number, title=title):
                table = section.split("\n## ", 1)[0]
                rows = re.findall(r"^\|\s*(\d+)\s*\|(.+)\|$",
                                  table, flags=re.MULTILINE)
                self.assertTrue(rows, "No numbered conditions found")
                self.assertEqual([int(item) for item, _ in rows],
                                 list(range(1, len(rows) + 1)))
                statuses = [row.rsplit("|", 1)[-1].strip()
                            for _, row in rows]
                for status in statuses:
                    self.assertRegex(status, r"^(済|一部|未)(（.+）)?$")
                done = sum(s.split("（", 1)[0] == "済" for s in statuses)
                self.assertEqual(score, f"{done}/{len(rows)} = "
                                        f"{100 * done / len(rows):.0f}%")
                complete += done
                total += len(rows)

        self.assertGreater(total, 0)
        summary = re.findall(r"^       = (.+)$", text, flags=re.MULTILINE)
        self.assertEqual(summary, [f"{complete}/{total} ≈ "
                                   f"{100 * complete / total:.0f}%"])
