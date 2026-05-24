import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "samba_utils.py"
SPEC = spec_from_file_location("samba_utils", MODULE_PATH)
samba_utils = module_from_spec(SPEC)
SPEC.loader.exec_module(samba_utils)
browse_directories = samba_utils.browse_directories


class TestPathBrowser(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "shares"
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "nested").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_open_root(self):
        result = browse_directories(str(self.root), [str(self.root)])
        self.assertEqual(result["current_path"], str(self.root.resolve()))
        self.assertIn("nested", [d["name"] for d in result["directories"]])

    def test_nested_directories(self):
        nested = self.root / "nested"
        result = browse_directories(str(nested), [str(self.root)])
        self.assertEqual(result["current_path"], str(nested.resolve()))
        self.assertEqual(result["parent"], str(self.root.resolve()))

    def test_block_path_outside_root(self):
        outside = Path(self.temp.name)
        with self.assertRaises(PermissionError):
            browse_directories(str(outside), [str(self.root)])

    def test_empty_directory(self):
        empty = self.root / "empty"
        empty.mkdir()
        result = browse_directories(str(empty), [str(self.root)])
        self.assertEqual(result["directories"], [])

    def test_missing_directory(self):
        missing = self.root / "missing"
        with self.assertRaises(FileNotFoundError):
            browse_directories(str(missing), [str(self.root)])

    def test_symlink_outside_is_blocked(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "secret").mkdir()
        (self.root / "link_out").symlink_to(outside, target_is_directory=True)
        result = browse_directories(str(self.root), [str(self.root)])
        self.assertNotIn("link_out", [d["name"] for d in result["directories"]])


if __name__ == "__main__":
    unittest.main()
