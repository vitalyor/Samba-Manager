import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "samba_utils.py"
SPEC = spec_from_file_location("samba_utils", MODULE_PATH)
samba_utils = module_from_spec(SPEC)
SPEC.loader.exec_module(samba_utils)


class TestPrepareUnplug(unittest.TestCase):
    def test_no_connections(self):
        with patch.object(samba_utils, "get_active_connections", return_value={"connections": []}):
            ok, msg = samba_utils.prepare_share_for_unplug("DATA")
        self.assertTrue(ok)
        self.assertIn("No active SMB clients", msg)

    def test_terminates_share_connections(self):
        states = [
            {"connections": [{"service": "DATA", "pid": "101", "machine": "mac"}]},
            {"connections": []},
        ]
        with patch.object(samba_utils, "get_active_connections", side_effect=states):
            with patch.object(samba_utils, "terminate_connection", return_value=(True, "ok")):
                ok, msg = samba_utils.prepare_share_for_unplug("DATA")
        self.assertTrue(ok)
        self.assertIn("Closed 1 connection", msg)


if __name__ == "__main__":
    unittest.main()
