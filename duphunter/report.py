"""查重结果输出：表格 / JSON / CSV 三种格式。"""

from __future__ import annotations

import csv
import io
import json
import sys
from typing import TextIO

from .finder import DuplicateSet
from .utils import human_size


def to_json(dup_sets: list[DuplicateSet], indent: int = 2) -> str:
    """序列化为 JSON 字符串。"""
    payload = {
        "total_duplicate_sets": len(dup_sets),
        "total_wasted_bytes": sum(d.wasted_bytes for d in dup_sets),
        "duplicate_sets": [
            {
                "hash": d.hash_value,
                "size": d.size,
                "files": d.files,
                "keep": d.keep,
                "victims": d.victims,
                "wasted_bytes": d.wasted_bytes,
            }
            for d in dup_sets
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=indent)


def to_csv(dup_sets: list[DuplicateSet]) -> str:
    """序列化为 CSV 字符串，每行一个文件。"""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["group", "size_bytes", "hash", "role", "path", "wasted_bytes"])
    for index, dup_set in enumerate(dup_sets, start=1):
        for path in dup_set.files:
            role = "keep" if path == dup_set.keep else "duplicate"
            writer.writerow(
                [index, dup_set.size, dup_set.hash_value, role, path, dup_set.wasted_bytes]
            )
    return buf.getvalue()


def to_table(dup_sets: list[DuplicateSet], stream: TextIO = sys.stdout) -> None:
    """以人类可读表格输出到指定流。"""
    if not dup_sets:
        print("未发现重复文件 ✔", file=stream)
        return

    total_wasted = sum(d.wasted_bytes for d in dup_sets)
    print(
        f"发现 {len(dup_sets)} 组重复文件，"
        f"冗余合计 {human_size(total_wasted)}",
        file=stream,
    )
    print("=" * 72, file=stream)
    for index, dup_set in enumerate(dup_sets, start=1):
        print(
            f"[组 {index}] {human_size(dup_set.size)} x {len(dup_set.files)} 份 | "
            f"可释放 {human_size(dup_set.wasted_bytes)}",
            file=stream,
        )
        for path in dup_set.files:
            mark = "保留 → " if path == dup_set.keep else "重复   "
            print(f"  {mark}{path}", file=stream)
        print("-" * 72, file=stream)
    print(f"合计可释放: {human_size(total_wasted)}", file=stream)
