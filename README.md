# 🏹 DupHunter

<p align="center">
  <b>简体中文</b> · <a href="#繁體中文">繁體中文</a> · <a href="#english">English</a>
</p>

跨平台重复文件查找与**安全清理**命令行工具 —— 🔍 体积预分组 + 内容精确哈希双阶段引擎，🛡️ 默认只报告不改动，5 种处理动作由你掌控。**100% Python 标准库，零强制依赖。**

> 💡 灵感来源：磁盘总在悄悄被复制粘贴填满。市面上多数去重工具要么粗放删除、要么依赖复杂环境，DupHunter 的目标是做一个"报告先行、动作可控、开箱即跑"的轻量去重利器。

---

## 🎉 项目介绍

**DupHunter** 帮你找出散落在目录各处、内容完全相同的重复文件，并按你的节奏安全清理。

**解决的痛点：**

- 😫 照片、下载、备份目录里同一份文件存了 N 份，磁盘白白浪费
- 😨 一般工具"一键清理"太粗暴，删错了找不回
- 🧩 环境依赖复杂，装个工具比干活还费劲

**自研差异化亮点：**

- 🧠 **双阶段查重引擎**：先按体积分组（体积不同内容必不同），仅对同体积文件做内容哈希，大目录扫描速度大幅提升
- 🛡️ **安全第一**：默认只输出报告；清理动作需显式指定，且内置交互确认
- 🔗 **硬链接去重**：物理删除冗余副本却保留目录结构 —— 所有路径依然存在，磁盘只占一份
- 📦 **零依赖**：核心功能全部基于 Python 标准库（BLAKE2b 哈希），3.9+ 直接运行
- ⚡ **并行扫描**：元数据采集与哈希计算均使用线程池，可调线程数

## ✨ 核心特性

- 🔍 **精准识别**：BLAKE2b 内容哈希，同体积不同内容绝不误判
- ⚡ **quick 模式**：超大文件仅哈希首尾分块预筛，速度优先
- 🧹 **5 种处理动作**：`report`（默认）/ `move`（隔离）/ `delete` / `hardlink` / `symlink`
- 📊 **3 种输出格式**：人类可读表格、JSON（可接脚本）、CSV（可进表格软件）
- 🚫 **灵活过滤**：glob 排除模式、最小体积阈值、符号链接跟随开关
- 🧵 **并行引擎**：`-j N` 自由调节线程数
- 💻 **跨平台**：Windows / macOS / Linux 全兼容

## 🚀 快速开始

**环境要求：** Python 3.9+（无其他依赖）

```bash
# 方式一：克隆仓库直接运行
git clone https://github.com/gitstq/duphunter.git
cd duphunter
python -m duphunter ~/Downloads          # 扫描下载目录（仅报告）

# 方式二：安装为命令行工具
pip install .
duphunter --version
```

## 📖 详细使用指南

### 常用命令示例

```bash
# 1️⃣ 只看报告（默认，绝不修改文件）
duphunter ~/照片 ~/下载

# 2️⃣ 排除临时文件，忽略小于 1MB 的文件
duphunter ~/项目 -e '*.tmp' -e '.git' --min-size 1048576

# 3️⃣ 输出 JSON 供脚本处理
duphunter ~/数据 -f json > report.json

# 4️⃣ 把重复文件移动到隔离区（安全，可随时取回）
duphunter ~/下载 -a move -t ~/隔离区 -y

# 5️⃣ 用硬链接消除冗余：路径保留，磁盘只存一份 ⭐ 推荐
duphunter ~/照片 -a hardlink -y

# 6️⃣ 大目录加速：quick 预筛 + 16 线程
duphunter ~/归档 --quick -j 16
```

### 参数速查

| 参数 | 说明 | 默认值 |
|---|---|---|
| `PATH...` | 要扫描的目录/文件（可多个） | 必填 |
| `-e, --exclude` | glob 排除模式，可重复 | 无 |
| `--min-size` | 忽略小于 N 字节的文件 | 1 |
| `-f, --format` | `table` / `json` / `csv` | table |
| `-a, --action` | `none`/`move`/`delete`/`hardlink`/`symlink` | none |
| `-t, --target-dir` | move 动作的隔离目录 | 无 |
| `-y, --yes` | 跳过交互确认 | 关 |
| `--quick` | 超大文件首尾分块快筛 | 关 |
| `-L, --follow-symlinks` | 跟随符号链接 | 关 |
| `-j, --jobs` | 并行线程数 | 8 |

### 典型场景

- 📸 **相册去重**：先 `-a move -t 隔离区` 观察几天，确认无误再清空隔离区
- 🗄️ **备份库瘦身**：`-a hardlink -y`，保留全部路径的同时释放磁盘
- 🤖 **自动化流水线**：`-f json` 供脚本读取，`-a delete -y` 配合 CI 定期清理

## 💡 设计思路与迭代规划

- **双阶段分组**：体积哈希碰撞概率为零（体积不同=内容不同），把昂贵的 IO 哈希只花在真正的候选集上
- **报告与动作分离**：查重是无副作用的纯函数，清理是显式的独立步骤，责任边界清晰
- **保留策略**：每组固定保留最短路径者，结果可预期、可复现

**后续迭代计划：**

- 🖼️ 相似图片识别（感知哈希）
- 📈 扫描结果缓存与增量比对
- 🖥️ 交互式 TUI 选择保留项

## 📦 打包与部署指南

```bash
# 构建分发包
pip install build
python -m build            # 生成 dist/*.whl 与 dist/*.tar.gz

# 全平台运行（仅要求 Python 3.9+）
python -m duphunter --help

# 运行测试
python -m unittest discover -s tests -v
```

兼容环境：Python 3.9 – 3.12，Windows 10+ / macOS 12+ / 主流 Linux 发行版。

## 🤝 贡献指南

欢迎 Issue 与 PR！提交信息遵循 Angular 规范（`feat:` / `fix:` / `docs:` …），新功能请附带单元测试，详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源，可自由使用、修改与分发。

---

<a id="繁體中文"></a>
## 🏹 DupHunter（繁體中文）

<p align="center">
  <a href="#-duphunter">简体中文</a> · <b>繁體中文</b> · <a href="#english">English</a>
</p>

跨平台重複檔案查找與**安全清理**命令列工具 —— 🔍 體積預分組 + 內容精確雜湊雙階段引擎，🛡️ 預設只報告不更動，5 種處理動作由你掌控。**100% Python 標準庫，零強制依賴。**

### 🎉 專案介紹

**DupHunter** 幫你找出散落在目錄各處、內容完全相同的重複檔案，並按你的節奏安全清理。

**解決的痛點：** 相簿與備份目錄重複檔案泛濫、一般工具清理太粗暴、環境依賴複雜。

**自研差異化亮點：**

- 🧠 **雙階段查重引擎**：先按體積分組，僅對同體積檔案計算內容雜湊
- 🛡️ **安全第一**：預設只輸出報告，清理動作需顯式指定並內建確認
- 🔗 **硬連結去重**：保留全部路徑，磁碟只佔一份
- 📦 **零依賴**：核心基於 Python 標準庫 BLAKE2b，3.9+ 直接執行
- ⚡ **並行掃描**：執行緒池可調

### ✨ 核心特性

🔍 精準識別 · ⚡ quick 快篩模式 · 🧹 5 種處理動作（report/move/delete/hardlink/symlink）· 📊 表格/JSON/CSV 輸出 · 🚫 glob 排除與體積過濾 · 💻 Windows/macOS/Linux 全相容

### 🚀 快速開始

```bash
git clone https://github.com/gitstq/duphunter.git
cd duphunter
python -m duphunter ~/Downloads     # 僅報告，不修改任何檔案

# 安裝為命令列工具
pip install .
duphunter ~/照片 -a hardlink -y     # 硬連結去重 ⭐ 推薦
```

### 📖 詳細使用

```bash
duphunter ~/資料 -f json > report.json        # JSON 輸出
duphunter ~/下載 -a move -t ~/隔離區 -y       # 移動到隔離區
duphunter ~/歸檔 --quick -j 16                # 大目錄加速
```

參數說明與簡體中文版一致：`-e` 排除模式、`--min-size` 最小體積、`-f` 輸出格式、`-a` 處理動作、`-y` 跳過確認。

### 💡 設計理念

體積分組零碰撞、報告與動作分離、保留策略可預期（每組保留最短路徑者）。後續規劃：相似圖片識別、增量掃描快取、互動式 TUI。

### 📦 打包與部署

```bash
python -m build && python -m unittest discover -s tests -v
```

相容 Python 3.9–3.12 與 Windows 10+ / macOS 12+ / 主流 Linux。

### 🤝 貢獻指南與 📄 開源協議

歡迎 Issue 與 PR（Angular 提交規範），詳見 [CONTRIBUTING.md](CONTRIBUTING.md)。基於 [MIT License](LICENSE) 開源。

---

<a id="english"></a>
## 🏹 DupHunter (English)

<p align="center">
  <a href="#-duphunter">简体中文</a> · <a href="#繁體中文">繁體中文</a> · <b>English</b>
</p>

A cross-platform CLI that **finds duplicate files and cleans them up safely** — 🔍 a two-stage engine (size pre-grouping + exact content hashing), 🛡️ report-only by default, with 5 optional cleanup actions under your control. **Pure Python standard library, zero mandatory dependencies.**

> 💡 Inspiration: disks quietly fill up with copy-pasted duplicates. Most dedup tools are either too aggressive or too heavy to install. DupHunter aims to be a lightweight tool that reports first and acts only when you say so.

### 🎉 Introduction

**DupHunter** locates files with identical content scattered across your directories and lets you clean them up at your own pace.

**Pain points solved:** duplicate photos/backups wasting disk, one-click cleaners that are too risky, and tools with heavy environment requirements.

**Differentiators:**

- 🧠 **Two-stage engine** — group by size first (different size = different content), hash only same-size candidates
- 🛡️ **Safety first** — report-only by default; destructive actions are explicit and confirmed
- 🔗 **Hardlink dedup** — keep every path on disk while storing the data only once
- 📦 **Zero dependencies** — built entirely on the standard library (BLAKE2b), runs on Python 3.9+
- ⚡ **Parallel scanning** — tunable thread pool

### ✨ Key Features

🔍 Exact matching · ⚡ quick mode (hash first/last chunks of huge files) · 🧹 5 actions (`report`/`move`/`delete`/`hardlink`/`symlink`) · 📊 table / JSON / CSV output · 🚫 glob excludes & size threshold · 💻 Windows / macOS / Linux

### 🚀 Quick Start

**Requirements:** Python 3.9+ (nothing else)

```bash
# Option 1: clone and run
git clone https://github.com/gitstq/duphunter.git
cd duphunter
python -m duphunter ~/Downloads            # report only

# Option 2: install as a CLI
pip install .
duphunter --version
```

### 📖 Usage Guide

```bash
duphunter ~/Photos ~/Downloads                        # 1️⃣ report only (never modifies)
duphunter ~/project -e '*.tmp' -e '.git' --min-size 1048576   # 2️⃣ filter noise
duphunter ~/data -f json > report.json                # 3️⃣ machine-readable output
duphunter ~/Downloads -a move -t ~/quarantine -y      # 4️⃣ quarantine duplicates
duphunter ~/Photos -a hardlink -y                     # 5️⃣ hardlink dedup ⭐ recommended
duphunter ~/archive --quick -j 16                     # 6️⃣ speed up huge trees
```

| Option | Description | Default |
|---|---|---|
| `PATH...` | Directories/files to scan | required |
| `-e, --exclude` | glob exclude pattern (repeatable) | none |
| `--min-size` | Skip files smaller than N bytes | 1 |
| `-f, --format` | `table` / `json` / `csv` | table |
| `-a, --action` | `none`/`move`/`delete`/`hardlink`/`symlink` | none |
| `-t, --target-dir` | Quarantine dir for `move` | none |
| `-y, --yes` | Skip confirmation prompt | off |
| `--quick` | Hash only first/last chunks of huge files | off |
| `-L, --follow-symlinks` | Follow symlinks | off |
| `-j, --jobs` | Worker threads | 8 |

**Typical scenarios:** 📸 quarantine first, verify, then purge · 🗄️ hardlink backup libraries to reclaim space · 🤖 JSON output for automation pipelines.

### 💡 Design & Roadmap

Size grouping has zero collisions; hashing IO is spent only on real candidates. Report and action are cleanly separated (pure functions vs. explicit steps). The keep-policy is deterministic: shortest path in each group.

**Roadmap:** 🖼️ similar-image detection (perceptual hash) · 📈 incremental scan cache · 🖥️ interactive TUI for keep-selection.

### 📦 Packaging & Deployment

```bash
pip install build && python -m build       # sdist + wheel
python -m duphunter --help                 # runs anywhere with Python 3.9+
python -m unittest discover -s tests -v    # run tests
```

Compatible with Python 3.9–3.12 on Windows 10+, macOS 12+, and mainstream Linux.

### 🤝 Contributing

Issues and PRs are welcome! Please follow Angular commit conventions (`feat:` / `fix:` / `docs:` …) and add tests for new features. See [CONTRIBUTING.md](CONTRIBUTING.md).

### 📄 License

Released under the [MIT License](LICENSE).
