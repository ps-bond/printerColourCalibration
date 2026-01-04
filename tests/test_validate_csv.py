import os
import tempfile
import unittest

from printer_calibration.validate_csv import validate


class TestValidateCSV(unittest.TestCase):
    def test_validate_ok(self):
        contents = """patch,rgb,L,a,b_lab
0,100,53.2,-0.5,1.2
1,150,67.1,0.1,-0.9
"""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(contents)
        try:
            validate(path)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
