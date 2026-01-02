import unittest

from printer_calibration.config import Targets, InkSteps


class TestConfig(unittest.TestCase):
    def test_defaults(self):
        t = Targets()
        self.assertEqual(t.a_neutral, 0.0)
        self.assertEqual(t.b_neutral, 0.0)
        self.assertTrue(t.a_tol > 0)

    def test_ink_steps(self):
        s = InkSteps()
        self.assertIsInstance(s.coarse, int)
        self.assertIsInstance(s.fine, int)


if __name__ == "__main__":
    unittest.main()
