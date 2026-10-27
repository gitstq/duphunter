"""重复文件查找核心：体积预分组 → 内容哈希精确分组。"""

from __future__ import annotations

import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .hasher import DEFAULT_ALGORITHM, hash_file
from .scanner import FileEntry


@dataclass
class DuplicateSet:
    """一组内容完全相同的文件。"""

    size: int
    hash_value: str
    files: list[str] = field(default_factory=list)

    @property
    def wasted_bytes(self) -> int:
        """该组可释放的冗余字节数（保留一份）。"""
        if len(self.files) < 2:
            return 0
        return self.size * (len(self.files) - 1)

    @property
    def keep(self) -> str:
        """默认保留项：路径最短者，路径长度相同取字典序最小者。"""
        return sorted(self.files, key=lambda p: (len(p), p))[0]

    @property
    def victims(self) -> list[str]:
        """默认待清理项：除保留项以外的全部文件。"""
        keep = self.keep
        return [p for p in self.files if p != keep]


def _hash_entry(entry: FileEntry, algorithm: str, quick: bool) -> tuple[str, str]:
    try:
        digest = hash_file(entry.path, algorithm=algorithm, quick=quick)
        return entry.path, digest
    except OSError:
        return entry.path, ""


def find_duplicates(
    entries: list[FileEntry],
    algorithm: str = DEFAULT_ALGORITHM,
    quick: bool = False,
    jobs: int = 8,
) -> list[DuplicateSet]:
    """在扫描结果中查找内容重复的文件集合。

    第一阶段按文件体积分组（体积不同内容必不同），
    第二阶段仅对同体积组计算内容哈希并精确分组。

    Returns:
        按冗余字节数降序的 DuplicateSet 列表。
    """
    by_size: dict[int, list[FileEntry]] = defaultdict(list)
    for entry in entries:
        by_size[entry.size].append(entry)

    dup_map: dict[str, list[str]] = defaultdict(list)
    size_of: dict[str, int] = {}

    for size, group in by_size.items():
        if len(group) < 2:
            continue
        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            results = pool.map(
                lambda e: _hash_entry(e, algorithm, quick), group
            )
        for path, digest in results:
            if not digest:
                continue  # 不可读文件跳过
            key = f"{size}:{digest}"
            dup_map[key].append(path)
            size_of[key] = size

    dup_sets = [
        DuplicateSet(size=size_of[key], hash_value=key.split(":", 1)[1], files=sorted(paths))
        for key, paths in dup_map.items()
        if len(paths) > 1
    ]
    dup_sets.sort(key=lambda d: (d.wasted_bytes, d.size), reverse=True)
    return dup_sets
