import os
import pwd
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "samba_utils.py"
SPEC = spec_from_file_location("samba_utils", MODULE_PATH)
samba_utils = module_from_spec(SPEC)
SPEC.loader.exec_module(samba_utils)
apply_share_access_policy = samba_utils.apply_share_access_policy


class TestShareAccessPolicy(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.share_path = Path(self.temp.name) / "share"
        self.share_path.mkdir(parents=True, exist_ok=True)
        self.username = pwd.getpwuid(os.getuid()).pw_name

    def tearDown(self):
        self.temp.cleanup()

    def test_auto_mode_keeps_force_empty_when_writable(self):
        share = {
            "path": str(self.share_path),
            "valid_users": self.username,
            "write_list": "",
            "read_only": "no",
            "force_user": "",
            "force_group": "",
            "access_mode": "auto",
        }
        updated, note = apply_share_access_policy(share)
        self.assertEqual(updated.get("force_user", ""), "")
        self.assertEqual(updated.get("force_group", ""), "")
        self.assertEqual(note, "")

    def test_auto_mode_falls_back_to_root_when_not_writable(self):
        os.chmod(self.share_path, 0o555)
        share = {
            "path": str(self.share_path),
            "valid_users": self.username,
            "write_list": "",
            "read_only": "no",
            "force_user": "",
            "force_group": "",
            "access_mode": "auto",
        }
        updated, note = apply_share_access_policy(share)
        self.assertEqual(updated.get("force_user"), "root")
        self.assertIn("force user = root", note)

    def test_manual_mode_preserves_force_values(self):
        share = {
            "path": str(self.share_path),
            "valid_users": self.username,
            "write_list": "",
            "read_only": "no",
            "force_user": "nobody",
            "force_group": "nogroup",
            "access_mode": "manual",
        }
        updated, note = apply_share_access_policy(share)
        self.assertEqual(updated.get("force_user"), "nobody")
        self.assertEqual(updated.get("force_group"), "nogroup")
        self.assertEqual(note, "")


if __name__ == "__main__":
    unittest.main()
