# Chatflow Tailor - Claude Agent for Workflow Generation

一个基于 Claude Agent SDK 的对话式工作流生成器,可以将自然语言描述转换为 Agent Studio 的 chatflow JSON 文件。

## 快速启动

### 1. 安装依赖

```bash
# Python 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install
```

### 2. 配置环境

确保 `.env` 文件包含 API 凭证:
```
BASE_URL=https://api.moonshot.cn/anthropic
API_KEY=your-api-key-here
```

### 3. 启动服务

**方式一: 分开启动**
```bash
# 终端 1: 启动后端 API (端口 8000)
python run_server.py

# 终端 2: 启动前端 (端口 3000)
cd frontend && npm run dev
```

**方式二: 仅命令行模式**
```bash
python -m src.main
```

### 4. 访问应用

打开浏览器访问 http://localhost:3000

- **左侧**: 与 Agent 对话,描述你想要的工作流
- **右侧**: 实时查看生成的流程图,支持缩放、编辑、添加节点

## 项目状态

✅ **Phase 1-4 完成** - 核心功能 + Web 前端 已实现 (100%)

### 已完成 ✅

**基础工具类:**
- `src/utils/config.py` - 环境配置加载器 (从 .env 加载 API 凭证)
- `src/utils/id_generator.py` - UUID 生成器 (支持单例和批量生成)
- `src/utils/position_calc.py` - 位置计算器 (自动布局节点)

**核心模块:**
- `src/core/variables.py` - 变量跟踪系统 (自动注册和管理变量)
- `src/core/edges.py` - 边连接逻辑 (管理节点间的连接)
- `src/core/workflow.py` - 主 Workflow 类 (编排所有组件,提供高级 API)

**生成器模块:**
- `src/generators/node_generator.py` - 所有节点类型生成 (start, textReply, captureUserReply, condition, code, llmVariableAssignment, llMReply)
- `src/generators/block_generator.py` - Block 包装器生成

**自然语言解析:**
- `src/parsers/intent_detector.py` - 意图检测器 (识别节点类型)
- `src/parsers/variable_extractor.py` - 变量提取器 (提取变量名)
- `src/parsers/nl_parser.py` - 主解析器 (自然语言 → 结构化步骤)

**Agent 集成:**
- `src/agent/tools.py` - Agent 工具定义 (4个工具函数)
- `src/agent/chatflow_agent.py` - Agent 对话循环
- `src/main.py` - 主入口程序 (支持交互式和快速模式)

**配置文件:**
- `requirements.txt` - Python 依赖列表
- 项目目录结构 (src/, output/, tests/)

### 当前功能

✅ **完整的编程式 API** - 可以通过 Python 代码直接构建 chatflow:

```python
from src.core.workflow import Workflow

# 创建 workflow
workflow = Workflow("customer_info", "收集客户信息")

# 添加节点
workflow.add_start_node()
workflow.add_text_reply("请问您的姓名?")
workflow.add_capture_user_reply("name", "用户姓名")
workflow.add_text_reply("感谢您,{{name}}!")

# 导出 JSON
json_str = workflow.to_json_string()
workflow.save("output/customer_info.json")

print(workflow.get_stats())
# Output: {'flow_name': 'customer_info', 'node_count': 7, 'edge_count': 3, 'variable_count': 1, 'has_start_node': True}
```

✅ **支持所有节点类型**:
- 基础节点: start, textReply, captureUserReply
- 逻辑节点: condition (支持多分支)
- 代码节点: code (Python 执行)
- LLM 节点: llmVariableAssignment, llMReply

✅ **自动化功能**:
- 自动位置计算 (无需手动指定坐标)
- 自动变量注册 (使用变量时自动添加到 variables 列表)
- 自动节点连接 (可选的 auto_connect 参数)
- 自动生成 UUID (节点 ID, Block ID, Handle ID 等)

✅ **自然语言解析** - 将自然语言描述转换为 workflow:

```python
from src.parsers.nl_parser import NLParser

parser = NLParser()
result = parser.parse("询问姓名,获取姓名,发送感谢")

# 输出: {'steps': [...], 'variables': [...], 'meta': {...}}
```

✅ **Claude Agent 集成** - 对话式生成 chatflow:

**交互模式** (推荐):
```bash
python -m src.main
```

**快速模式** (单次生成):
```bash
python -m src.main --quick "询问姓名,获取姓名,发送感谢" --name greeting
```

### 待优化 📋

- `src/generators/validator.py` - 更完善的 JSON 验证
- 更智能的条件分支解析
- 支持更复杂的循环结构

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API 凭证
# 确保 .env 文件包含:
# BASE_URL=https://api.moonshot.cn/anthropic
# API_KEY=your-api-key-here
```

## 使用方法 (开发完成后)

### 对话式交互

```bash
python src/main.py
```

Agent 会引导你通过自然语言描述工作流,然后自动生成 JSON 文件到 `output/` 目录。

### 编程式调用

```python
from src.agent.chatflow_agent import ChatflowAgent
from src.utils.config import get_config

config = get_config()
agent = ChatflowAgent(api_key=config.api_key, base_url=config.base_url)

result = agent.quick_generate(
    description="询问姓名,获取姓名,询问邮箱,获取邮箱,发送感谢",
    workflow_name="customer_info"
)

print(f"生成完成: {result['filepath']}")
```

## 架构设计

### 核心理念

- **对话式交互**: 通过自然对话理解需求
- **Tool-use Pattern**: 使用 Claude SDK 的工具调用机制
- **模块化设计**: 每个组件职责单一,易于测试和扩展
- **可扩展性**: 支持生成 100+ 节点的大规模 flow

### 技术栈

- **Claude Agent SDK**: anthropic >= 0.40.0
- **环境管理**: python-dotenv
- **JSON 验证**: jsonschema
- **测试框架**: pytest

### 支持的节点类型

**基础节点:**
- `start` - 工作流入口点
- `textReply` - 发送文本消息
- `captureUserReply` - 捕获用户输入

**逻辑节点:**
- `condition` - 条件分支 (支持多分支)

**处理节点:**
- `code` - Python 代码执行

**LLM 节点:**
- `llmVariableAssignment` - LLM 提取并赋值变量
- `llMReply` - LLM 直接回复用户

**包装节点:**
- `block` - 功能节点的可视化包装器

## 开发指南

### 项目结构

```
chatflow-tailor/
├── .env                    # API 凭证
├── data/                   # 示例 JSON 文件
├── output/                 # 生成的 JSON 输出
├── src/
│   ├── agent/              # Claude Agent 实现
│   ├── core/               # 核心领域逻辑
│   ├── generators/         # JSON 生成器
│   ├── parsers/            # 自然语言解析
│   └── utils/              # 工具类
├── tests/                  # 测试套件
└── requirements.txt        # 依赖
```

### 运行测试

```bash
pytest tests/
```

### 代码风格

- 使用类型提示 (type hints)
- 遵循 PEP 8 规范
- 函数和类都有文档字符串

## 参考文档

- [Claude Agent SDK 文档](https://platform.claude.com/docs/en/agent-sdk/python)
- [实现计划](.claude/plans/foamy-crunching-raccoon.md)
- [示例 JSON 文件](data/)

## License

MIT

## 作者

Generated with Claude Code
