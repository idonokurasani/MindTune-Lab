import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = ROOT / "scripts" / "build_mindtune_native_app.sh"


class NativeBundleContractTests(unittest.TestCase):
    def test_capture_runtime_includes_all_local_imports(self) -> None:
        source = BUILD_SCRIPT.read_text(encoding="utf-8")

        for filename in (
            "fc11_mac_capture.py",
            "fc11_capture_pipeline.py",
            "lsl_bridge.py",
            "scientific_qc.py",
            "scientific_spectral.py",
            "scientific_longitudinal.py",
        ):
            self.assertIn(filename, source)

    def test_build_requires_verified_pylsl_runtime(self) -> None:
        source = BUILD_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("PYLSL_SITE=", source)
        self.assertIn("exit 3", source)


if __name__ == "__main__":
    unittest.main()
