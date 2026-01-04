import os
import tempfile
import unittest

from printer_calibration.charts import generate_neutral_chart, generate_colour_chart


class TestCharts(unittest.TestCase):
    def test_generate_neutral_chart(self):
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            generate_neutral_chart(path, dpi=72)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)
        finally:
            os.remove(path)

    def test_generate_colour_chart(self):
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            generate_colour_chart(path=path)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
