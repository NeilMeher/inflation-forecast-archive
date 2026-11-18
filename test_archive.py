import unittest
import archive


class ArchiveTests(unittest.TestCase):
    def test_reference_quarter_and_overlap(self):
        rows, scores = archive.evaluate(archive.load())
        self.assertEqual(len(rows), 5)
        self.assertAlmostEqual(rows[0]["actual"], (0.25+0.71+1.33)/3)
        self.assertAlmostEqual(rows[0]["baseline"], 3.16)
        self.assertAlmostEqual(rows[-1]["baseline"], 0.25)
        self.assertEqual(set(scores), {"mpc", "survey", "baseline"})
        self.assertTrue(all(r["baseline_month"] < r["date"][:7] for r in rows))
