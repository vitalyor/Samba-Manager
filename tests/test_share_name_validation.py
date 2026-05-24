import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "routes.py"
HAS_FLASK = importlib.util.find_spec("flask") is not None
routes = None
if HAS_FLASK:
    SPEC = spec_from_file_location("routes", MODULE_PATH)
    routes = module_from_spec(SPEC)
    SPEC.loader.exec_module(routes)


@unittest.skipUnless(HAS_FLASK, "Flask is required to import routes module")
class TestShareNameValidation(unittest.TestCase):
    def test_allows_cyrillic_and_spaces(self):
        ok, _ = routes.validate_share_name("2 ТБ")
        self.assertTrue(ok)

    def test_blocks_forbidden_chars(self):
        ok, msg = routes.validate_share_name("bad/name")
        self.assertFalse(ok)
        self.assertIn("forbidden", msg.lower())


if __name__ == "__main__":
    unittest.main()
