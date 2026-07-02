import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "samba_utils.py"
SPEC = spec_from_file_location("samba_utils", MODULE_PATH)
samba_utils = module_from_spec(SPEC)
SPEC.loader.exec_module(samba_utils)


class TestReconcileWaitingDisk(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.share_conf = self.base / "shares.conf"
        self.profile_conf = self.base / "share_profiles.json"
        self.online_path = self.base / "online-share"
        self.online_path.mkdir(parents=True, exist_ok=True)
        self.missing_path = self.base / "missing-share"

        self.orig_share_conf = samba_utils.SHARE_CONF
        self.orig_profile_conf = samba_utils.SHARE_PROFILE_CONF
        self.orig_dev_mode = samba_utils.DEV_MODE

        samba_utils.SHARE_CONF = str(self.share_conf)
        samba_utils.SHARE_PROFILE_CONF = str(self.profile_conf)
        samba_utils.DEV_MODE = True

    def tearDown(self):
        samba_utils.SHARE_CONF = self.orig_share_conf
        samba_utils.SHARE_PROFILE_CONF = self.orig_profile_conf
        samba_utils.DEV_MODE = self.orig_dev_mode
        self.temp.cleanup()

    def test_offline_path_share_not_published(self):
        doc = {
            "version": 1,
            "shares": [
                {
                    "name": "ONLINE",
                    "enabled": True,
                    "mode": "path",
                    "disk": {"disk_id": "", "partuuid": "", "uuid": "", "serial": "", "wwn": ""},
                    "relative_path": "/",
                    "resolved_path": str(self.online_path),
                    "runtime_state": "unknown",
                    "share": {
                        "path": str(self.online_path),
                        "browseable": "yes",
                        "read_only": "no",
                        "guest_ok": "no",
                        "valid_users": "vitalyor",
                    },
                },
                {
                    "name": "OFFLINE",
                    "enabled": True,
                    "mode": "path",
                    "disk": {"disk_id": "", "partuuid": "", "uuid": "", "serial": "", "wwn": ""},
                    "relative_path": "/",
                    "resolved_path": str(self.missing_path),
                    "runtime_state": "unknown",
                    "share": {
                        "path": str(self.missing_path),
                        "browseable": "yes",
                        "read_only": "no",
                        "guest_ok": "no",
                        "valid_users": "vitalyor",
                    },
                },
            ],
        }
        samba_utils._save_profile_doc(doc)

        with patch.object(samba_utils, "_validate_shares_content", return_value=True):
            ok = samba_utils.reconcile_share_profiles_once()
        self.assertTrue(ok)

        rendered = self.share_conf.read_text()
        self.assertIn("[ONLINE]", rendered)
        self.assertNotIn("[OFFLINE]", rendered)

        ui_shares = {s["name"]: s for s in samba_utils.list_managed_shares()}
        self.assertEqual(ui_shares["ONLINE"]["runtime_state"], "online")
        self.assertEqual(ui_shares["OFFLINE"]["runtime_state"], "offline")

    def test_offline_to_online_triggers_session_refresh(self):
        doc = {
            "version": 1,
            "shares": [
                {
                    "name": "OFFLINE",
                    "enabled": True,
                    "mode": "path",
                    "disk": {"disk_id": "", "partuuid": "", "uuid": "", "serial": "", "wwn": ""},
                    "relative_path": "/",
                    "resolved_path": str(self.missing_path),
                    "runtime_state": "unknown",
                    "share": {
                        "path": str(self.missing_path),
                        "browseable": "yes",
                        "read_only": "no",
                        "guest_ok": "no",
                        "valid_users": "vitalyor",
                    },
                }
            ],
        }
        samba_utils._save_profile_doc(doc)

        with patch.object(samba_utils, "_validate_shares_content", return_value=True):
            first_ok = samba_utils.reconcile_share_profiles_once()
        self.assertTrue(first_ok)

        self.missing_path.mkdir(parents=True, exist_ok=True)

        with patch.object(samba_utils, "_validate_shares_content", return_value=True):
            with patch.object(
                samba_utils, "_reset_share_sessions_after_reconnect"
            ) as reset_mock:
                second_ok = samba_utils.reconcile_share_profiles_once()

        self.assertTrue(second_ok)
        reset_mock.assert_called_once_with("OFFLINE")

    def test_udevil_stub_not_published_then_recovers(self):
        # Путь существует, но внутри маркер udevil = реальный диск НЕ смонтирован.
        stub_path = self.base / "stub-share"
        stub_path.mkdir(parents=True, exist_ok=True)
        marker = stub_path / ".udevil-mount-point"
        marker.write_text("")

        doc = {
            "version": 1,
            "shares": [
                {
                    "name": "STUB",
                    "enabled": True,
                    "mode": "path",
                    "disk": {"disk_id": "", "partuuid": "", "uuid": "", "serial": "", "wwn": ""},
                    "relative_path": "/",
                    "resolved_path": str(stub_path),
                    "runtime_state": "unknown",
                    "share": {
                        "path": str(stub_path),
                        "browseable": "yes",
                        "read_only": "no",
                        "guest_ok": "no",
                        "valid_users": "vitalyor",
                    },
                }
            ],
        }
        samba_utils._save_profile_doc(doc)

        with patch.object(samba_utils, "_validate_shares_content", return_value=True):
            self.assertTrue(samba_utils.reconcile_share_profiles_once())

        self.assertNotIn("[STUB]", self.share_conf.read_text())
        ui = {s["name"]: s for s in samba_utils.list_managed_shares()}
        self.assertEqual(ui["STUB"]["runtime_state"], "offline")
        self.assertTrue(ui["STUB"]["runtime_note"])

        # Диск примонтировался поверх → маркер исчезает → шара публикуется + refresh.
        marker.unlink()
        with patch.object(samba_utils, "_validate_shares_content", return_value=True):
            with patch.object(
                samba_utils, "_reset_share_sessions_after_reconnect"
            ) as reset_mock:
                self.assertTrue(samba_utils.reconcile_share_profiles_once())

        self.assertIn("[STUB]", self.share_conf.read_text())
        reset_mock.assert_called_once_with("STUB")


if __name__ == "__main__":
    unittest.main()
