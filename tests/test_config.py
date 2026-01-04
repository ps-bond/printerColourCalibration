import unittest

from printer_calibration.config import Phase1Targets, InkSteps


class TestConfig(unittest.TestCase):
    def test_phase1_targets(self):
        t = Phase1Targets()
        a_neutral = (t.a_range[0] + t.a_range[1]) / 2
        b_neutral = (t.b_range[0] + t.b_range[1]) / 2
        a_tol = (t.a_range[1] - t.a_range[0]) / 2
        self.assertEqual(a_neutral, 0.0)
        self.assertEqual(b_neutral, 0.0)
        self.assertTrue(a_tol > 0)

    def test_ink_steps(self):
        s = InkSteps()
        self.assertIsInstance(s.coarse, int)
        self.assertIsInstance(s.fine, int)


if __name__ == "__main__":
    unittest.main()
