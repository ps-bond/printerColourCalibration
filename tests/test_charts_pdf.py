import os
import tempfile
import unittest


class TestChartsPDF(unittest.TestCase):
    def test_neutral_chart_pdf_save(self):
        from printer_calibration import charts

        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tf.close()
        try:
            charts.generate_neutral_chart(tf.name, format="PDF")
            self.assertTrue(os.path.exists(tf.name))
            self.assertGreater(os.path.getsize(tf.name), 0)
        finally:
            try:
                os.remove(tf.name)
            except OSError:
                pass

    def test_workflow_generate_chart_pdf(self):
        from printer_calibration import workflow

        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tf.close()
        try:
            workflow.generate_chart("neutral", filename=tf.name, format="PDF")
            self.assertTrue(os.path.exists(tf.name))
            self.assertGreater(os.path.getsize(tf.name), 0)
        finally:
            try:
                os.remove(tf.name)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
