import os
import tempfile
import unittest

from PIL import Image


class TestChartTitles(unittest.TestCase):
    def _sample_top_center_nonwhite(self, img_path):
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        x = w // 2
        y = min(40, max(5, h // 20))
        box = img.crop((x - 5, y - 5, x + 5, y + 5))
        pixels = list(box.getdata())
        return any(px != (255, 255, 255) for px in pixels)

    def test_generate_neutral_chart_with_title(self):
        from printer_calibration import charts

        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tf.close()
        try:
            charts.generate_neutral_chart(tf.name, title="Neutral Title Test")
            self.assertTrue(os.path.exists(tf.name))
            self.assertGreater(os.path.getsize(tf.name), 0)
            self.assertTrue(self._sample_top_center_nonwhite(tf.name))
        finally:
            try:
                os.remove(tf.name)
            except OSError:
                pass

    def test_generate_colour_chart_with_title(self):
        from printer_calibration import charts

        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tf.close()
        try:
            charts.generate_colour_chart(tf.name, title="Colour Title Test")
            self.assertTrue(os.path.exists(tf.name))
            self.assertGreater(os.path.getsize(tf.name), 0)
            self.assertTrue(self._sample_top_center_nonwhite(tf.name))
        finally:
            try:
                os.remove(tf.name)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
