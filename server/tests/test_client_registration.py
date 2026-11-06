import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from voice_changer.VoiceChangerManager import VoiceChangerManager
from voice_changer.utils.LoadModelParams import LoadModelParams, LoadModelParamFile


class SafeRegistrationTest(unittest.TestCase):
    def make_manager(self, model_dir):
        manager = VoiceChangerManager.__new__(VoiceChangerManager)
        manager.params = SimpleNamespace(model_dir=str(model_dir))
        manager._model_registration_lock = threading.RLock()
        manager._load_model = Mock(return_value={"status": "OK"})
        return manager

    def params(self, name="model.pth", slot=0):
        return LoadModelParams("RVC", slot, False, "", [LoadModelParamFile(name, "rvcModel", "")], {})

    def test_concurrent_empty_registration_reserves_one_slot_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "uploads").mkdir()
            (root / "uploads/model.pth").write_bytes(b"owned fixture")
            managers = [self.make_manager(root / "models") for _ in range(2)]
            barrier = threading.Barrier(2)

            def register(manager):
                barrier.wait()
                try:
                    manager.loadModel(self.params(), require_empty=True)
                    return "registered"
                except FileExistsError:
                    return "occupied"

            with patch("voice_changer.VoiceChangerManager.UPLOAD_DIR", str(root / "uploads")):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(register, managers))
            self.assertCountEqual(results, ["registered", "occupied"])
            self.assertEqual(sum(manager._load_model.call_count for manager in managers), 1)
            winner = next(manager for manager in managers if manager._load_model.called)
            self.assertFalse(winner._load_model.call_args.kwargs["replace_existing"])

    def test_partial_import_and_existing_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "uploads").mkdir()
            (root / "uploads/model.pth").write_bytes(b"owned fixture")
            manager = self.make_manager(root / "models")
            manager._load_model.side_effect = RuntimeError("fixture failure")
            with patch("voice_changer.VoiceChangerManager.UPLOAD_DIR", str(root / "uploads")):
                with self.assertRaises(RuntimeError):
                    manager.loadModel(self.params(), require_empty=True)
                proof = root / "models/0/preserved.txt"
                proof.write_text("preserve", encoding="utf-8")
                with self.assertRaises(FileExistsError):
                    manager.loadModel(self.params(), require_empty=True)
                self.assertEqual(proof.read_text(encoding="utf-8"), "preserve")

    def test_legacy_call_keeps_existing_overwrite_semantics(self):
        manager = self.make_manager("unused")
        manager.loadModel(self.params())
        self.assertTrue(manager._load_model.call_args.kwargs["replace_existing"])

    def test_safe_registration_rejects_paths_and_invalid_slots(self):
        manager = self.make_manager("unused")
        for params in [self.params("../model.pth"), self.params(slot=-1), self.params(slot=500)]:
            with self.assertRaises(ValueError):
                manager.loadModel(params, require_empty=True)
        manager._load_model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
