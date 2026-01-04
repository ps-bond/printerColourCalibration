import unittest
import pandas as pd

from printer_calibration.analysis import suggest_adjustment
from printer_calibration.config import InkSteps, Phase1Targets


class TestAnalysis(unittest.TestCase):
    # def test_neutral_error(self):
    #     df = pd.DataFrame({
    #         "patch": [0, 1, 2],
    #         "rgb": [100, 150, 50],
    #         "L": [50, 60, 30],
    #         "a": [0.1, -0.1, 1.0],
    #         "b": [0.2, -0.2, 0.5],
    #     })
    #     a_mean, b_mean = neutral_error(df)
    #     # mean of a for rgb 100 and 150 is (0.1 + -0.1)/2 == 0.0
    #     self.assertAlmostEqual(a_mean, 0.0)
    #     self.assertAlmostEqual(b_mean, 0.0)

    def test_suggest_adjustment(self):
        steps = InkSteps(coarse=4, fine=1)
        targets = Phase1Targets()
        # Test case for fine 'M' and coarse 'Y' adjustment
        patch_lab = (50, -3.0, -9.0)
        adj = suggest_adjustment(patch_lab=patch_lab, targets=targets, steps=steps)
        self.assertEqual(adj.get("M", 0), 4)
        self.assertEqual(adj.get("Y", 0), 4)
        self.assertEqual(adj.get("C", 0), 0)


if __name__ == "__main__":
    unittest.main()
