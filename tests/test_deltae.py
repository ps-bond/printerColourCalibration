import unittest

from printer_calibration.deltae import delta_e


class TestDeltaE(unittest.TestCase):
    def test_delta_e_zero(self):
        # Identical Lab values should give zero deltaE
        val = delta_e((50, 0, 0), (50, 0, 0))
        self.assertAlmostEqual(val, 0.0)


if __name__ == "__main__":
    unittest.main()
