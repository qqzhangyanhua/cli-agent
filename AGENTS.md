# Repository Guidelines

## 项目结构与模块组织
- 入口：根目录 `dnm` 为 CLI 入口脚本（安装后可直接用 `dnm` 命令）
- `src/` 核心代码：`core/` 流程与执行，`mcp/` MCP 集成，`tools/` 工具与适配，`ui/` 交互层；`__init__.py` 声明包
- `test/` PyTest 用例；根目录含补充测试 `test_enhanced_features.py`
- `scripts/` 安装与卸载脚本：`install.py`、`install.sh`、`uninstall.sh`
- `docs/` 文档说明；`daily_reports/` 日报；`knowledge/` 知识库
- 配置：`config.template.json` → 复制为 `config.json`（勿入库）；依赖：`requirements.txt`
```text
./dnm
src/{core,mcp,tools,ui}/
test/test_*.py
scripts/{install.py,install.sh,uninstall.sh}
docs/, FEATURE_ARCHITECTURE.md
config.template.json → config.json
```

## 构建、测试与本地运行
```bash
pip install -r requirements.txt    # 安装依赖
python install.py                  # 安装 CLI（或 ./install.sh）
dnm --help                         # 验证安装
pytest -q                          # 运行全部测试
python terminal_agent.py           # 本地交互演示
./dnm "列出所有Python文件"         # 从仓库根直接调用入口
dnm -w . "显示git状态"              # 指定工作目录运行
dnm "检查开发环境"                   # 快速诊断依赖与配置
```

## 代码风格与命名约定
- Python 3.8+；PEP 8；缩进 4 空格；`snake_case` 函数/变量，`PascalCase` 类；模块置于 `src/`
- 推荐工具：`black`、`ruff`（可选）；提交前保证无明显 lint/格式问题
- 测试文件命名：`test_*.py`；文档放入 `docs/`
- 注释与文档统一使用中文，保持术语一致
- 异常处理：对用户输出清晰错误信息；核心路径记录日志便于排查
- 分支命名：`feature/*`、`fix/*`、`refactor/*`，一事一分支

## 测试指南
- 框架：PyTest；用例集中于 `test/`，命名 `test_*.py`
- 覆盖率：关键模块（`src/core`, `src/mcp`）建议 ≥80%；新增功能需配套测试
- 原则：用临时文件/假数据，禁止测试访问外部网络与真实密钥；按需使用 `pytest -k 关键字` 过滤

## Commit 与 Pull Request 规范
- 提交信息遵循 Conventional Commits：`feat|fix|refactor|docs|chore` 等；中文简述，允许 Emoji
- PR 要求：清晰描述、关联 Issue、列出变更点/影响面；附运行步骤与截图/日志；确保 `pytest -q` 通过；涉及配置/文档的同步更新 `docs/`
- 变更核心流程或模块关系时，请同步更新 `FEATURE_ARCHITECTURE.md`
- 建议小而聚焦的 PR，确保可回滚；如涉及 CLI 行为变更，请在描述中附示例命令

## 安全与配置提示（可选）
- 切勿提交 `config.json` 或任何密钥；以 `config.template.json` 为模板本地填写
- 跨平台与编码：命令执行相关代码注意 Windows/UTF-8 兼容（参见 `docs/WINDOWS_ENCODING_FIX.md`）

## 架构与文档
- 项目说明：`FEATURE_ARCHITECTURE.md` 提供系统架构、核心模块与交互流程的权威说明
- 修改建议：新增能力前先评估对 `src/core`、`src/mcp` 的影响；如涉及路由/流程，请补充示意图与关键路径说明
- 关键约定：CLI 入口、模块职责、数据流与错误处理策略以该文档为准，提交前务必通读并对照自检
