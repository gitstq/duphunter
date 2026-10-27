# 🔨

```bash
make test      # 运行全部单元测试
make build     # 构建 sdist + wheel
make clean     # 清理构建产物
```

等效命令（Windows PowerShell 可直接执行，无需 make）：

```powershell
python -m unittest discover -s tests -v
pip install build && python -m build
```
