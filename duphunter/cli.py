"""DupHunter 命令行界面。"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .actions import ActionError, apply_action
from .finder import find_duplicates
from .hasher import available_algorithms
from .report import to_csv, to_json, to_table
from .scanner import scan
from .utils import human_size, iter_unique_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="duphunter",
        description="DupHunter — 跨平台重复文件查找与安全清理工具（纯标准库实现）",
    )
    parser.add_argument(
        "paths", nargs="+", metavar="PATH",
        help="要扫描的目录或文件（可多个）",
    )
    parser.add_argument(
        "-e", "--exclude", action="append", default=[],
        help="glob 排除模式，可重复使用，例如 -e '*.tmp' -e '.git'",
    )
    parser.add_argument(
        "--min-size", type=int, default=1, metavar="BYTES",
        help="小于该字节数的文件跳过（默认 1，即忽略空文件）",
    )
    parser.add_argument(
        "-L", "--follow-symlinks", action="store_true",
        help="跟随符号链接（默认不跟随，避免死循环）",
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="超大文件仅哈希首尾分块以加速（结果可能需二次确认）",
    )
    parser.add_argument(
        "--algorithm", default="blake2b", choices=available_algorithms(),
        help="内容哈希算法（默认 blake2b）",
    )
    parser.add_argument(
        "-f", "--format", default="table", choices=["table", "json", "csv"],
        help="输出格式（默认 table）",
    )
    parser.add_argument(
        "-j", "--jobs", type=int, default=8, metavar="N",
        help="并行线程数（默认 8）",
    )
    parser.add_argument(
        "-a", "--action", default="none",
        choices=["none", "move", "delete", "hardlink", "symlink"],
        help="对重复文件执行的动作（默认 none 仅报告）",
    )
    parser.add_argument(
        "-t", "--target-dir", metavar="DIR",
        help="action=move 时重复文件的隔离目录",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="跳过确认提示，直接执行动作",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    roots = iter_unique_paths(args.paths)
    if not roots:
        print("错误：没有可用的扫描路径", file=sys.stderr)
        return 2

    entries = scan(
        roots,
        exclude=args.exclude,
        min_size=args.min_size,
        follow_symlinks=args.follow_symlinks,
        jobs=args.jobs,
    )
    dup_sets = find_duplicates(
        entries, algorithm=args.algorithm, quick=args.quick, jobs=args.jobs
    )

    if args.format == "json":
        print(to_json(dup_sets))
    elif args.format == "csv":
        print(to_csv(dup_sets).rstrip("\n"))
    else:
        to_table(dup_sets)

    if args.action != "none":
        try:
            result = apply_action(
                dup_sets, action=args.action, target_dir=args.target_dir, assume_yes=args.yes
            )
        except ActionError as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1
        print(
            f"动作完成: 移动 {result.moved} | 删除 {result.deleted} | "
            f"链接 {result.linked} | 失败 {len(result.errors)}"
        )
        for err in result.errors:
            print(f"  [失败] {err}", file=sys.stderr)
        if result.errors:
            return 1

    if dup_sets and args.format == "table":
        print(f"提示: 冗余合计 {human_size(sum(d.wasted_bytes for d in dup_sets))}")
    return 0
