import unittest

from printer_calibration.convergence import plot


class TestConvergence(unittest.TestCase):
    def test_plot_runs(self):
        # Ensure plot doesn't raise when given simple history data.
        history = {"a_mean": [0, 1, 0], "b_mean": [0, -1, 0]}
        # Call plot; visually it would show, but here we only confirm it runs.
        plot(history)


if __name__ == "__main__":
    unittest.main()
