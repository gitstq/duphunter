"""文件内容哈希。

默认使用 BLAKE2b（标准库内置，安全且快）。quick 模式仅读取首尾各一个分块，
适合超大文件的快速预筛，但可能产生极低概率的误判，最终结果仍以全量哈希为准。
"""

from __future__ import annotations

import hashlib
import os

DEFAULT_ALGORITHM = "blake2b"
DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MiB

def available_algorithms() -> list[str]:
    """返回当前运行环境可用的哈希算法列表。"""
    return sorted(
        name
        for name in ("blake2b", "blake2s", "sha256", "sha1", "md5")
        if name in hashlib.algorithms_available
    )


def hash_file(
    path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    algorithm: str = DEFAULT_ALGORITHM,
    quick: bool = False,
) -> str:
    """计算文件哈希。

    Args:
        path: 文件路径。
        chunk_size: 分块大小（字节）。
        algorithm: 哈希算法名。
        quick: 为 True 且文件大于 2 个分块时，仅哈希首尾两个分块，
               返回值以 ``-q`` 结尾以便识别（快速模式结果）。

    Returns:
        十六进制哈希字符串；文件不可读时抛出 OSError。
    """
    h = hashlib.new(algorithm)
    size = os.path.getsize(path)
    if quick and size > chunk_size * 2:
        with open(path, "rb") as f:
            h.update(f.read(chunk_size))
            f.seek(-chunk_size, os.SEEK_END)
            h.update(f.read(chunk_size))
        return h.hexdigest() + "-q"
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()
