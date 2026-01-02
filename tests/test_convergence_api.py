import os
import tempfile
import unittest

import matplotlib.pyplot as plt


class TestConvergenceAPI(unittest.TestCase):
    def test_plot_returns_figure_and_manual_close(self):
        from printer_calibration.convergence import plot, close

        history = {"metric": [0, 1, 0]}
        fig = plot(history, auto_close=False)
        # Should be a Figure instance
        from matplotlib.figure import Figure

        self.assertIsInstance(fig, Figure)

        # Figure should exist until we close it
        self.assertTrue(plt.fignum_exists(fig.number))
        close(fig)
        self.assertFalse(plt.fignum_exists(fig.number))

    def test_plot_savepath_writes_file(self):
        from printer_calibration.convergence import plot

        history = {"a": [1, 2, 3], "b": [3, 2, 1]}
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tf.close()
        try:
            plot(history, savepath=tf.name)
            self.assertTrue(os.path.exists(tf.name))
            self.assertGreater(os.path.getsize(tf.name), 0)
        finally:
            try:
                os.remove(tf.name)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
