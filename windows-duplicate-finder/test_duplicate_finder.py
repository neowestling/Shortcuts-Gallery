import importlib.util
import tempfile
import unittest
from pathlib import Path

source = Path(__file__).with_name("duplicate_finder.py")
spec = importlib.util.spec_from_file_location("finder", source)
finder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finder)

class ScanTests(unittest.TestCase):
    def test_duplicate_and_distinct(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.txt").write_bytes(b"hello")
            (root / "b.txt").write_bytes(b"hello")
            (root / "c.txt").write_bytes(b"world")
            groups, count, errors = finder.find_duplicates(root)
            self.assertEqual(count, 3)
            self.assertFalse(errors)
            self.assertEqual(len(groups), 1)
            self.assertEqual({p.name for p in groups[0][2]}, {"a.txt", "b.txt"})

    def test_empty_files_and_subfolders(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "sub").mkdir()
            (root / "a").touch()
            (root / "sub" / "b").touch()
            groups, count, errors = finder.find_duplicates(root)
            self.assertEqual(count, 2)
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0][0], 0)
            self.assertFalse(errors)

    def test_same_size_different_content(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a").write_bytes(b"ABC")
            (root / "b").write_bytes(b"XYZ")
            groups, count, errors = finder.find_duplicates(root)
            self.assertEqual((groups, count, errors), ([], 2, []))

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(finder.find_duplicates(Path(d)), ([], 0, []))

if __name__ == "__main__":
    unittest.main()
