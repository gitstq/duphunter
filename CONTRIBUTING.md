# 贡献指南 / Contributing Guide

感谢关注 DupHunter！欢迎以 Issue 或 PR 的形式参与贡献。

## 🐛 反馈缺陷

1. 先检索已有 Issue，避免重复提交
2. 新 Issue 请包含：操作系统与 Python 版本、完整复现命令、预期行为与实际行为
3. 如涉及崩溃，请附上完整错误堆栈

## 🌟 提交代码

1. Fork 仓库并创建特性分支：`git checkout -b feat/your-feature`
2. 遵循 Angular 提交规范：
   - `feat:` 新增功能
   - `fix:` 修复缺陷
   - `docs:` 文档更新
   - `refactor:` 代码重构
   - `test:` 测试补充
   - `chore:` 工程配置
3. 核心代码仅使用 Python 标准库，不引入强制第三方依赖
4. 为新功能补充对应的单元测试（tests/ 目录）
5. 提交前确保 `python -m unittest discover -s tests` 全部通过
6. 发起 Pull Request 并清晰描述改动动机与影响范围

## 📐 代码风格

- 模块级中文 docstring，函数级类型标注（typing）
- 每个模块职责单一，保持 scanner / hasher / finder / actions / report / cli 的分层边界

再次感谢你的贡献！
