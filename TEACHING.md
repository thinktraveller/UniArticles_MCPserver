# Teaching Log

## Step 12: 发布 0.3.0 版本 (Release 0.3.0)

### 1) 变更内容
更新项目版本号为 `0.3.0`，以反映近期移除 ChemRxiv 模块及其他改进。

- **修改文件**:
  - `pyproject.toml`: 将 `version` 字段从 `0.2.0` 更新为 `0.3.0`。
  - `src/uniarticles/__init__.py`: 添加 `__version__ = "0.3.0"` 变量，便于在代码中获取版本信息。

### 2) 验证
- 检查 `pyproject.toml` 确认版本号已更新。
- 检查 `src/uniarticles/__init__.py` 确认包含版本信息。

Next, run:
$ uv build
