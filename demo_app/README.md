# ResearchOS 学习引擎 · 本地演示工具

零依赖的轻量级本地演示工具，用于验证高分文章学习库（High-Impact Paper
Learning Library）和项目记忆巩固（Sleep Cycle）两条 pipeline。

## 目的

无需 ResearchOS 后端、无需真实 LLM、无需外部服务，即可在浏览器中直观查看
两条核心 pipeline 的输出。所有处理使用内置的 `MockLLMAdapter`，结果确定
可复现。

## 启动方式

在项目根目录下执行：

```bash
PYTHONPATH=src python3 demo_app/server.py
```

启动后访问 **http://127.0.0.1:8766**。

可选环境变量：
- `DEMO_PORT` — 修改端口号（默认 8766）
- `DEMO_HOST` — 修改绑定地址（默认 127.0.0.1）

## 使用说明

### 高分文章学习库（Tab 1）

1. 从下拉菜单选择示例文章
   - `B. subtilis FPR Paper` — 内置的高分文章示例
   - `Real Case — case_001 / 002 / 003` — 真实文章风格的测试文本
2. 可在编辑器中修改文章 JSON
3. 填写项目 ID 和项目描述
4. 点击**「学习这篇文章」**
5. 右侧展示结果：质量分/相关分卡片、实验设计、信号机制、图表逻辑、写作模式、可复用洞察
6. 点击**「导出 JSON」**保存结果到 `examples/outputs/demo_exports/`

### 项目记忆巩固（Tab 2）

1. 选择 `Sleep Cycle — Cancer Metabolism` 示例
2. 可在编辑器中修改 ConsolidationInput JSON
3. 点击**「运行记忆巩固」**
4. 右侧展示：提升/归档/取代记忆数量、新模式、证据边、项目摘要、推荐文献查询、处理日志
5. 点击**「导出 JSON」**保存结果

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 引擎版本、Schema 版本 |
| GET | `/api/examples` | 列出可加载的示例文件 |
| GET | `/api/example?name=xxx` | 加载指定示例 JSON |
| POST | `/api/paper/learn` | 运行 `learn_high_impact_paper()` |
| POST | `/api/sleep-cycle` | 运行 `run_sleep_cycle()` |
| POST | `/api/export` | 保存结果到 `outputs/demo_exports/` |

## 运行测试

```bash
# 全部测试（包含服务端测试）
python3 run_tests.py

# 仅服务端测试
python3 -m unittest tests.test_demo_app_server -v
```

## 当前限制

- 使用 `MockLLMAdapter` — 输出是确定性模板，非真实 LLM 提取。
  生产环境请通过环境变量配置真实 LLM（见主 README）。
- 不支持 PDF 上传或解析 — 文章文本需通过 JSON 提供。
- 无真实文献检索 — 巩固阶段的推荐基于规则模板。
- 无用户认证或多用户支持 — 纯本地工具。
- JSON 编辑器为纯文本 textarea — 无语法高亮或校验。

## 未来接入 ResearchOS

本演示工具为独立开发工具。当学习引擎合入主 ResearchOS 后端后：

- `server.py` 中的 API 端点将替换为 ResearchOS 后端的 HTTP 框架。
- `MockLLMAdapter` 将替换为生产 LLM 适配器。
- 前端可嵌入 ResearchOS 仪表盘。
- PDF 解析、文献检索、用户认证由 ResearchOS 主服务提供。
