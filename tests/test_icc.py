import os
import tempfile
import unittest

# from printer_calibration.icc import export_srgb_icc


class TestICC(unittest.TestCase):
    pass
    # def test_export_srgb_icc(self):
    #     fd, path = tempfile.mkstemp(suffix=".icc")
    #     os.close(fd)
    #     try:
    #         export_srgb_icc(path)
    #         self.assertTrue(os.path.exists(path))
    #         self.assertGreater(os.path.getsize(path), 0)
    #     finally:
    #         os.remove(path)


if __name__ == "__main__":
    unittest.main()
