"""目录扫描：收集文件条目（路径、大小、修改时间）。

支持多路径、排除模式（fnmatch）、最小体积过滤、符号链接控制，
并使用线程池并行获取文件元数据以提升大目录扫描速度。
"""

from __future__ import annotations

import fnmatch
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass(frozen=True)
class FileEntry:
    """单个待比对文件的信息。"""

    path: str
    size: int
    mtime: float


def _is_excluded(rel_path: str, name: str, patterns: tuple[str, ...]) -> bool:
    """判断文件或目录是否命中排除模式。"""
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(rel_path, pattern):
            return True
    return False


def _stat_entry(path: str, follow: bool) -> FileEntry | None:
    """获取单个文件的元数据；失败返回 None。"""
    try:
        st = os.stat(path) if follow else os.lstat(path)
        if not os.path.isfile(path):
            return None
        return FileEntry(path=path, size=st.st_size, mtime=st.st_mtime)
    except OSError:
        return None


def scan(
    roots: list[str],
    exclude: list[str] | None = None,
    min_size: int = 1,
    follow_symlinks: bool = False,
    jobs: int = 8,
) -> list[FileEntry]:
    """递归扫描一个或多个根路径，返回文件条目列表。

    Args:
        roots: 要扫描的根目录（或文件）列表。
        exclude: glob 排除模式，例如 ["*.tmp", ".git"]。
        min_size: 小于该字节数的文件将被跳过（默认 1，即忽略空文件）。
        follow_symlinks: 是否跟随符号链接目录与文件。
        jobs: 并行 stat 的线程数。

    Returns:
        按 (size, path) 排序的 FileEntry 列表。
    """
    patterns = tuple(exclude or ())
    candidates: list[str] = []

    for root in roots:
        if os.path.isfile(root):
            candidates.append(root)
            continue
        for dirpath, dirnames, filenames in os.walk(
            root, followlinks=follow_symlinks
        ):
            # 原地过滤需要继续下钻的目录
            dirnames[:] = [
                d
                for d in dirnames
                if not _is_excluded(
                    os.path.relpath(os.path.join(dirpath, d), root), d, patterns
                )
            ]
            for name in filenames:
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root)
                if _is_excluded(rel, name, patterns):
                    continue
                candidates.append(full)

    entries: list[FileEntry] = []
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        for entry in pool.map(lambda p: _stat_entry(p, follow_symlinks), candidates):
            if entry is not None and entry.size >= min_size:
                entries.append(entry)

    entries.sort(key=lambda e: (e.size, e.path))
    return entries
