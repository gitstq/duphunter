"""DupHunter — 跨平台重复文件查找与安全清理工具包。

纯 Python 标准库实现，零第三方依赖（tqdm 进度条为可选增强）。
"""

from .finder import find_duplicates
from .scanner import scan

__version__ = "1.0.0"
__author__ = "gitstq"

__all__ = ["__version__", "__author__", "scan", "find_duplicates"]
