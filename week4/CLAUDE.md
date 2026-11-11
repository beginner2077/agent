# more-itertools 工作指南

## 项目与定位

这是扩展 Python itertools 的可迭代对象工具库，支持 Python >=3.11，没有需要启动的 Web 服务。
`more_itertools/__init__.py` 从 `more.py` 和 `recipes.py` 导出公共接口；新增公共工具时核对所属模块的 `__all__`。
`more_itertools/*.pyi` 与 `py.typed` 是维护中的类型接口；修改公共签名时同步核对，不能当生成文件删除。
`tests/test_more.py`、`tests/test_recipes.py` 对应两个实现模块；`docs/api.rst` 组织 API 文档，函数示例主要位于源码 docstring。

## 命令

以下命令面向本课程 Windows 副本，均在仓库根目录执行，使用 `.venv` 中的 Python >=3.11。
完整开发工具按需安装，测试本身可直接从本地源码运行：

```text
./.venv/Scripts/python.exe -m pip install -r requirements/development.txt
./.venv/Scripts/python.exe -m pip install --editable .
```

全部测试（含 load_tests 加入的 doctest）：

```text
./.venv/Scripts/python.exe -m unittest -v
```

聚焦一个模块或测试类：

```text
./.venv/Scripts/python.exe -m unittest -v tests.test_more
./.venv/Scripts/python.exe -m unittest -v tests.test_more.ChunkedTests
```

聚焦范围按实际类/模块报告：上述类命令运行整个 `ChunkedTests`（包括既有用例），不执行模块级 `load_tests()`，不含额外注册的源码 doctest；模块命令会加载对应 doctest。

安装开发工具后，按改动选择检查；完整 CI 定义见 `.github/workflows/python-app.yml` 和 `Makefile`：

```text
./.venv/Scripts/python.exe -m ruff format --check .
./.venv/Scripts/python.exe -m ruff check more_itertools tests
./.venv/Scripts/python.exe -m mypy.stubtest more_itertools.more more_itertools.recipes
./.venv/Scripts/python.exe -m coverage run --include="more_itertools/*.py" -m unittest
./.venv/Scripts/python.exe -m coverage report --show-missing --fail-under=99
./.venv/Scripts/python.exe -m sphinx -W -b html docs docs/_build/html
./.venv/Scripts/python.exe -m flit build
./.venv/Scripts/python.exe -m twine check dist/*
```

库的最小运行示例：

```text
./.venv/Scripts/python.exe -c "from more_itertools import chunked; print(list(chunked(range(5), 2)))"
```

## 实现与验证约定

- 测试沿用 `unittest.TestCase`、`self.assert*` 和 `import more_itertools as mi`，放入对应工具的测试类。
- 迭代器行为测试需要实际消费结果；延迟抛出的异常要在消费时断言，参照 `ChunkedTests` 的 strict 用例。
- 不把测试入口默认换成 pytest；现有 `load_tests()` 负责将源码示例加入测试。
- 格式以 `pyproject.toml` 的 Ruff 配置为准：4 空格、行宽79、保留已有引号风格；不要套用其他项目的88列或全仓改引号。
- 单元测试、99%覆盖率、静态检查、文档构建和打包分别报告结果；缺工具或未运行的项目明确标注。

## 修改边界

- 修改源码、类型声明、测试和 `.rst` 文档源文件；不要手改 `docs/_build/`、`dist/`、`build/`、`.coverage` 或虚拟环境产物。
- 普通函数任务不顺带修改 `setup.cfg` 的版本配置、包版本号或 `.github/workflows/`；只在任务明确涉及这些内容时处理。
- 此 fork 用于课程练习；上游贡献规则在 `README.rst` 的 Development 节，课程任务不授权向上游创建 Issue、PR 或发布包。
