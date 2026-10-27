"""安全清理动作：报告（默认）/ 移动隔离 / 删除 / 硬链接 / 符号链接。

安全原则：
- 默认不做任何修改，仅输出报告；
- 硬链接/符号链接不跨文件系统（跨盘时自动回退并提示）；
- 删除与移动要求显式 --yes 或交互确认；
- 保留项始终是每个重复组中最短路径的那个文件。
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

from .finder import DuplicateSet
from .utils import is_subpath


class ActionError(RuntimeError):
    """清理动作执行失败。"""


@dataclass
class ActionResult:
    moved: int = 0
    deleted: int = 0
    linked: int = 0
    errors: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def _safe_remove(path: str) -> None:
    """删除文件；失败抛出 ActionError。"""
    try:
        os.remove(path)
    except OSError as exc:
        raise ActionError(f"无法删除 {path}: {exc}") from exc


def _check_same_device(keep: str, victim: str) -> None:
    """硬链接/符号链接要求与保留项位于同一文件系统。"""
    if os.path.exists(keep) and os.path.exists(victim):
        try:
            if os.stat(keep).st_dev != os.stat(victim).st_dev:
                raise ActionError(
                    f"跨文件系统无法链接: {victim} 与保留项 {keep} 不在同一设备"
                )
        except OSError as exc:
            raise ActionError(f"无法获取文件设备信息 {victim}: {exc}") from exc


def apply_action(
    dup_sets: list[DuplicateSet],
    action: str,
    target_dir: str | None = None,
    assume_yes: bool = False,
) -> ActionResult:
    """对全部重复组执行指定动作。

    Args:
        dup_sets: 查重结果。
        action: none | move | delete | hardlink | symlink。
        target_dir: action=move 时的隔离目录。
        assume_yes: 为 True 时跳过交互确认。

    Returns:
        ActionResult，含成功/失败计数。
    """
    result = ActionResult()
    if action in (None, "none"):
        return result

    if action == "move" and not target_dir:
        raise ActionError("move 动作必须提供 target_dir")

    victims: list[tuple[str, str]] = []  # (victim, keep)
    for dup_set in dup_sets:
        keep = dup_set.keep
        for victim in dup_set.victims:
            victims.append((victim, keep))

    if not victims:
        return result

    if not assume_yes:
        answer = input(
            f"将对 {len(victims)} 个重复文件执行 {action}，确认请输入 y: "
        ).strip().lower()
        if answer not in ("y", "yes"):
            print("已取消操作。")
            return result

    os.makedirs(target_dir, exist_ok=True) if action == "move" and target_dir else None

    for victim, keep in victims:
        try:
            if action == "move":
                assert target_dir is not None
                if is_subpath(victim, target_dir):
                    raise ActionError(f"目标目录包含待处理文件，跳过: {victim}")
                base = os.path.basename(victim)
                dest = os.path.join(target_dir, base)
                stem, ext = os.path.splitext(base)
                counter = 1
                while os.path.exists(dest):
                    dest = os.path.join(target_dir, f"{stem}_{counter}{ext}")
                    counter += 1
                shutil.move(victim, dest)
                result.moved += 1
            elif action == "delete":
                _safe_remove(victim)
                result.deleted += 1
            elif action == "hardlink":
                _check_same_device(keep, victim)
                _safe_remove(victim)
                os.link(keep, victim)
                result.linked += 1
            elif action == "symlink":
                _check_same_device(keep, victim)
                _safe_remove(victim)
                os.symlink(os.path.abspath(keep), victim)
                result.linked += 1
            else:
                raise ActionError(f"未知动作: {action}")
        except ActionError as exc:
            result.errors.append(str(exc))
        except OSError as exc:
            result.errors.append(f"{victim}: {exc}")

    return result
