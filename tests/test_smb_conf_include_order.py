import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "samba_utils.py"
SPEC = spec_from_file_location("samba_utils", MODULE_PATH)
samba_utils = module_from_spec(SPEC)
SPEC.loader.exec_module(samba_utils)
render_config_sections = samba_utils.render_config_sections


class TestSmbConfIncludeOrder(unittest.TestCase):
    def test_include_is_last_directive_in_global(self):
        sections = {
            "global": {
                "include": "/etc/samba/shares.conf",
                "server string": "Samba Server",
                "workgroup": "WORKGROUP",
            },
            "share1": {"path": "/shares/share1", "read only": "no"},
        }

        config = render_config_sections(sections, include_path="/etc/samba/shares.conf")
        global_block = config.split("[global]\n", 1)[1].split("\n[", 1)[0].strip()
        global_lines = [line.strip() for line in global_block.splitlines() if line.strip()]

        self.assertTrue(global_lines[-1].startswith("include = /etc/samba/shares.conf"))
        self.assertIn("server string = Samba Server", global_lines)
        self.assertIn("workgroup = WORKGROUP", global_lines)


if __name__ == "__main__":
    unittest.main()
