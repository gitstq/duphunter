"""DupHunter 单元测试（仅使用标准库 unittest）。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from duphunter.actions import ActionError, apply_action  # noqa: E402
from duphunter.finder import find_duplicates  # noqa: E402
from duphunter.hasher import hash_file  # noqa: E402
from duphunter.report import to_csv, to_json, to_table  # noqa: E402
from duphunter.scanner import scan  # noqa: E402
from duphunter.utils import human_size, is_subpath  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="duphunter_test_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def touch(self, relpath: str, content: bytes) -> str:
        path = os.path.join(self.tmp, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path


class TestHasher(unittest.TestCase):
    def test_same_content_same_hash(self):
        with tempfile.NamedTemporaryFile(delete=False) as a, \
             tempfile.NamedTemporaryFile(delete=False) as b:
            a.write(b"hello world"); b.write(b"hello world")
            pa, pb = a.name, b.name
        self.addCleanup(os.remove, pa); self.addCleanup(os.remove, pb)
        self.assertEqual(hash_file(pa), hash_file(pb))

    def test_diff_content_diff_hash(self):
        with tempfile.NamedTemporaryFile(delete=False) as a, \
             tempfile.NamedTemporaryFile(delete=False) as b:
            a.write(b"aaa"); b.write(b"bbb")
            pa, pb = a.name, b.name
        self.addCleanup(os.remove, pa); self.addCleanup(os.remove, pb)
        self.assertNotEqual(hash_file(pa), hash_file(pb))

    def test_quick_mode_stable_and_flags(self):
        data = os.urandom(5 * 1024 * 1024)  # 5 MiB，触发 quick 路径
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(data); path = f.name
        self.addCleanup(os.remove, path)
        quick1 = hash_file(path, quick=True)
        quick2 = hash_file(path, quick=True)
        self.assertEqual(quick1, quick2)          # 同文件结果稳定
        self.assertTrue(quick1.endswith("-q"))    # 带 quick 标记
        self.assertNotEqual(quick1, hash_file(path))  # 与全量哈希可区分

    def test_quick_mode_groups_duplicates_identically(self):
        data = os.urandom(3 * 1024 * 1024)
        with tempfile.NamedTemporaryFile(delete=False) as a, \
             tempfile.NamedTemporaryFile(delete=False) as b:
            a.write(data); b.write(data)
            pa, pb = a.name, b.name
        self.addCleanup(os.remove, pa); self.addCleanup(os.remove, pb)
        self.assertEqual(hash_file(pa, quick=True), hash_file(pb, quick=True))


class TestScanner(Base):
    def test_scan_finds_files(self):
        self.touch("a.txt", b"x" * 10)
        self.touch("sub/b.txt", b"y" * 10)
        entries = scan([self.tmp])
        self.assertEqual(len(entries), 2)

    def test_exclude_and_min_size(self):
        self.touch("keep.txt", b"data")
        self.touch("skip.tmp", b"data")
        self.touch("empty.txt", b"")
        entries = scan([self.tmp], exclude=["*.tmp"], min_size=1)
        names = {os.path.basename(e.path) for e in entries}
        self.assertEqual(names, {"keep.txt"})


class TestFinder(Base):
    def test_detects_duplicates(self):
        self.touch("a.bin", b"same")
        self.touch("b.bin", b"same")
        self.touch("c.bin", b"other")
        entries = scan([self.tmp])
        dups = find_duplicates(entries)
        self.assertEqual(len(dups), 1)
        self.assertEqual(len(dups[0].files), 2)
        self.assertEqual(dups[0].wasted_bytes, 4)

    def test_keep_and_victims(self):
        self.touch("long/dir/name.bin", b"same")
        self.touch("short.bin", b"same")
        dups = find_duplicates(scan([self.tmp]))
        self.assertEqual(dups[0].keep, os.path.join(self.tmp, "short.bin"))
        self.assertEqual(len(dups[0].victims), 1)

    def test_no_duplicates(self):
        self.touch("a.txt", b"1")
        self.touch("b.txt", b"22")
        self.assertEqual(find_duplicates(scan([self.tmp])), [])


class TestActions(Base):
    def _make_dups(self):
        self.touch("a.bin", b"content")
        self.touch("b.bin", b"content")
        self.touch("c.bin", b"content")
        return find_duplicates(scan([self.tmp]))

    def test_move(self):
        target = os.path.join(self.tmp, "quarantine")
        dups = self._make_dups()
        result = apply_action(dups, "move", target_dir=target, assume_yes=True)
        self.assertEqual(result.moved, 2)
        remaining = [f for _, _, files in os.walk(self.tmp) for f in files]
        self.assertEqual(len(remaining), 3)  # 保留 1 + 隔离 2

    def test_delete(self):
        dups = self._make_dups()
        result = apply_action(dups, "delete", assume_yes=True)
        self.assertEqual(result.deleted, 2)
        self.assertTrue(os.path.exists(dups[0].keep))

    def test_hardlink(self):
        dups = self._make_dups()
        result = apply_action(dups, "hardlink", assume_yes=True)
        self.assertEqual(result.linked, 2)
        self.assertEqual(os.stat(dups[0].keep).st_nlink, 3)

    def test_symlink(self):
        dups = self._make_dups()
        result = apply_action(dups, "symlink", assume_yes=True)
        self.assertEqual(result.linked, 2)
        self.assertTrue(os.path.islink(dups[0].victims[0]))

    def test_move_requires_target(self):
        dups = self._make_dups()
        with self.assertRaises(ActionError):
            apply_action(dups, "move", assume_yes=True)

    def test_none_is_noop(self):
        dups = self._make_dups()
        result = apply_action(dups, "none", assume_yes=True)
        self.assertEqual((result.moved, result.deleted, result.linked), (0, 0, 0))


class TestReport(Base):
    def setUp(self):
        super().setUp()
        self.touch("a.txt", b"dup")
        self.touch("b.txt", b"dup")
        self.dups = find_duplicates(scan([self.tmp]))

    def test_json_structure(self):
        payload = json.loads(to_json(self.dups))
        self.assertEqual(payload["total_duplicate_sets"], 1)
        self.assertEqual(payload["duplicate_sets"][0]["wasted_bytes"], 3)

    def test_csv_roles(self):
        lines = to_csv(self.dups).strip().splitlines()
        self.assertEqual(len(lines), 3)  # 表头 + 2 文件
        roles = [line.split(",")[3] for line in lines[1:]]
        self.assertCountEqual(roles, ["keep", "duplicate"])

    def test_table_output(self):
        import io
        buf = io.StringIO()
        to_table(self.dups, stream=buf)
        self.assertIn("组 1", buf.getvalue())


class TestUtils(unittest.TestCase):
    def test_human_size(self):
        self.assertEqual(human_size(0), "0 B")
        self.assertEqual(human_size(1024), "1.00 KB")
        self.assertEqual(human_size(1024 * 1024), "1.00 MB")

    def test_is_subpath(self):
        self.assertTrue(is_subpath("/a/b/c", "/a/b"))
        self.assertFalse(is_subpath("/a/x", "/a/b"))


class TestCLI(Base):
    def _run(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = os.path.dirname(self.tmp.split("duphunter_test_")[0]) \
            if False else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return subprocess.run(
            [sys.executable, "-m", "duphunter", *args],
            capture_output=True, text=True, env=env,
        )

    def test_table_mode(self):
        self.touch("a.txt", b"same")
        self.touch("b.txt", b"same")
        proc = self._run(self.tmp)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("组 1", proc.stdout)

    def test_json_mode(self):
        self.touch("a.txt", b"same")
        self.touch("b.txt", b"same")
        proc = self._run(self.tmp, "-f", "json")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["total_duplicate_sets"], 1)

    def test_csv_mode(self):
        self.touch("a.txt", b"same")
        self.touch("b.txt", b"same")
        proc = self._run(self.tmp, "-f", "csv")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("keep", proc.stdout)

    def test_delete_action_with_yes(self):
        self.touch("a.txt", b"same")
        self.touch("b.txt", b"same")
        proc = self._run(self.tmp, "-a", "delete", "-y")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("删除 1", proc.stdout)


if __name__ == "__main__":
    unittest.main()
