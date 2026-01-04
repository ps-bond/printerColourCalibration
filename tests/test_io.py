import os
import tempfile
import unittest

from printer_calibration.io import load_csv


class TestLoadCSV(unittest.TestCase):
    def write_temp(self, contents: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(contents)
        return path

    def test_load_valid_csv(self):
        contents = """patch,rgb,L,a,b_lab
0,100,53.2,-0.5,1.2
1,150,67.1,0.1,-0.9
"""
        path = self.write_temp(contents)
        try:
            df = load_csv(path)
            self.assertIn("patch", df.columns)
            self.assertIn("L", df.columns)
            self.assertIn("a", df.columns)
            self.assertIn("b", df.columns)
        finally:
            os.remove(path)

    def test_load_missing_column_raises(self):
        contents = """patch,rgb,L,a
0,100,53.2,-0.5
"""
        path = self.write_temp(contents)
        try:
            with self.assertRaises(ValueError):
                load_csv(path)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
