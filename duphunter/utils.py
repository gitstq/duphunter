"""通用工具函数。"""

from __future__ import annotations

import os
import sys
from typing import Iterable


def human_size(num_bytes: int) -> str:
    """将字节数转换为人类可读字符串，例如 1.5 MB。"""
    if num_bytes < 0:
        raise ValueError("字节数不能为负")
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PB"


def iter_unique_paths(paths: Iterable[str]) -> list[str]:
    """去重并保持顺序地归一化一组路径，校验存在性。"""
    seen: set[str] = set()
    result: list[str] = []
    for raw in paths:
        path = os.path.abspath(os.path.expanduser(raw))
        if path in seen:
            continue
        if not os.path.exists(path):
            print(f"[警告] 路径不存在，已跳过: {path}", file=sys.stderr)
            continue
        seen.add(path)
        result.append(path)
    return result


def is_subpath(child: str, parent: str) -> bool:
    """判断 child 是否位于 parent 目录之内（含相等）。"""
    child = os.path.abspath(child)
    parent = os.path.abspath(parent)
    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:
        # Windows 跨盘符等情况
        return False
