import os
import unittest

from printer_calibration.workflow import run, generate_chart


class TestWorkflow(unittest.TestCase):
    def test_run_on_example(self):
        # use the included example CSV from project root
        example = os.path.join(os.path.dirname(__file__), "..", "example_measurements.csv")
        example = os.path.normpath(example)
        a, b, adj = run(example)
        # a and b should be numeric
        self.assertIsInstance(a, float)
        self.assertIsInstance(b, float)
        self.assertIsInstance(adj, dict)

    def test_generate_chart_no_error(self):
        # ensure chart generation function runs without exception
        generate_chart("neutral")

    def test_generate_all_charts(self):
        # generate all charts into a temporary directory and verify files
        import tempfile

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            try:
                generate_chart("neutral", all_charts=True, format="PDF")
                self.assertTrue(os.path.exists("neutral_chart.pdf"))
                self.assertTrue(os.path.exists("colour_test_A4.pdf"))
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
