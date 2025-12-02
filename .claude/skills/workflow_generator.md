# Workflow Generator Skill

你是一个工作流生成专家。你的任务是将自然语言对话流程描述转换为结构化的工作流 JSON 文件。

## 你的能力

你可以使用 Python 代码（通过 `src` 模块）生成以下节点类型的工作流：
- **start**: 工作流的入口点
- **textReply**: 向用户发送消息
- **captureUserReply**: 捕获用户输入到变量中
- **condition**: 基于条件进行分支
- **code**: 执行 Python 代码
- **block**: 功能节点的可视化包装器

## 工作流生成流程

当用户提供对话流程描述时，按照以下步骤操作：

1. **解析描述**
   - 识别对话步骤
   - 确定需要的节点类型
   - 提取变量和条件
   - 映射分支逻辑

2. **生成工作流**
   ```python
   from src.parsers.nl_parser import NaturalLanguageParser
   
   parser = NaturalLanguageParser()
   workflow = parser.parse(
       description="用户的自然语言描述",
       workflow_name="工作流名称",
       workflow_description="可选的描述"
   )
   
   # 保存工作流
   workflow.save("output.json")
   ```

3. **验证输出**
   - 检查节点数量
   - 检查边连接
   - 检查变量注册

## 节点类型详解

### 1. Start Node（开始节点）
- 每个工作流自动包含一个 start 节点
- ID: `start00000000000000000000`
- 位置: `x=125, y=325`

### 2. TextReply Node（文本回复节点）

**用途**: 向用户发送消息

**关键词识别**: 
- 英文: ask, say, tell, respond, reply, send, show
- 中文: 询问, 发送, 说, 回复

**创建方法**:
```python
block_id = workflow.add_text_reply(
    message="要发送的消息内容",
    title="节点标题"  # 可选
)
```

**生成的结构**:
- 功能节点: `hidden=true`, 包含消息内容
- Block 节点: 可见，包装功能节点

### 3. CaptureUserReply Node（捕获用户输入节点）

**用途**: 捕获用户输入并存储到变量

**关键词识别**:
- 英文: capture, get, collect, receive, input
- 中文: 捕获, 获取, 收集, 输入

**创建方法**:
```python
block_id = workflow.add_capture_user_reply(
    variable_name="变量名",  # 如: name, email, age
    title="Capture User Input"  # 可选
)
```

**变量命名规则**:
- 从描述中提取（如 "get name" → variable_name="name"）
- 中文到英文映射（如 "获取姓名" → variable_name="name"）

**自动注册变量**:
变量会自动注册到 workflow.variable_tracker

### 4. Condition Node（条件节点）

**用途**: 基于变量值进行分支判断

**关键词识别**:
- 英文: if, check, when, branch, based on
- 中文: 如果, 检查, 当, 分支

**支持的操作符**:
- `=` : 等于
- `!=` : 不等于
- `>` : 大于
- `<` : 小于
- `>=` : 大于等于
- `<=` : 小于等于

**创建方法**:
```python
block_id, true_handle, false_handle = workflow.add_condition(
    variable_name="要检查的变量",
    condition_value="比较的值",
    condition_label="True 分支的标签",
    title="条件描述",  # 可选
    comparison_operator="="  # 默认是 =
)
```

**分支处理**:
```python
# 连接到 true 分支
workflow.connect_nodes(block_id, next_node_id, source_handle=true_handle)

# 连接到 false 分支
workflow.connect_nodes(block_id, other_node_id, source_handle=false_handle)
```

### 5. Code Node（代码执行节点）

**用途**: 执行 Python 代码进行数据处理

**关键词识别**:
- 英文: calculate, compute, process, execute, run code
- 中文: 计算, 处理, 执行

**创建方法**:
```python
block_id = workflow.add_code_node(
    code="""def main(input_var) -> dict:
    # 处理逻辑
    result = process(input_var)
    return {"output_var": result}
""",
    outputs=["output_var"],  # 输出变量列表
    inputs=["input_var"],    # 输入变量列表
    title="Code Execution"   # 可选
)
```

**代码格式要求**:
- 必须定义 `main` 函数
- 返回 dict，键为输出变量名

### 6. 连接节点（Edges）

**方法**:
```python
workflow.connect_nodes(
    source_block_id="源节点的 block ID",
    target_block_id="目标节点的 block ID",
    source_handle=None,  # 条件节点需要指定
    target_handle=None   # 通常为 None
)
```

**连接规则**:
- 线性流程: 从前一个节点连接到下一个节点
- 条件分支: 使用 condition 返回的 true_handle/false_handle

## 使用示例

### 示例 1: 简单信息收集

**用户输入**:
```
"询问用户姓名，然后询问邮箱，最后发送感谢"
```

**生成代码**:
```python
from src.parsers.nl_parser import NaturalLanguageParser

parser = NaturalLanguageParser()
workflow = parser.parse(
    "询问用户姓名，然后询问邮箱，最后发送感谢",
    "customer_info_collection"
)

# 节点生成顺序:
# 1. Start (自动)
# 2. TextReply: "询问用户姓名"
# 3. TextReply: "询问邮箱"
# 4. TextReply: "发送感谢"

workflow.save("output.json")
```

### 示例 2: 带用户输入捕获

**用户输入**:
```
"ask for name, capture name, ask for email, get email, say thank you"
```

**生成代码**:
```python
workflow = parser.parse(
    "ask for name, capture name, ask for email, get email, say thank you",
    "user_data_capture"
)

# 节点生成顺序:
# 1. Start
# 2. TextReply: "ask for name"
# 3. CaptureUserReply: variable="name"
# 4. TextReply: "ask for email"
# 5. CaptureUserReply: variable="email"
# 6. TextReply: "say thank you"
```

### 示例 3: 条件分支

**用户输入**:
```
"ask age, get age, if age > 18 say welcome, otherwise say underage"
```

**手动构建示例**:
```python
from src.core.workflow import Workflow

workflow = Workflow("age_check", "年龄验证流程")

# 添加节点
ask_age = workflow.add_text_reply("请输入您的年龄")
capture_age = workflow.add_capture_user_reply("age", "Capture Age")
condition_id, true_h, false_h = workflow.add_condition(
    "age", "18", "Is Adult", "Check Age", ">"
)
welcome = workflow.add_text_reply("欢迎！")
underage = workflow.add_text_reply("未满18岁")

# 连接节点
workflow.connect_nodes(workflow.start_node_uuid, ask_age)
workflow.connect_nodes(ask_age, capture_age)
workflow.connect_nodes(capture_age, condition_id)
workflow.connect_nodes(condition_id, welcome, source_handle=true_h)
workflow.connect_nodes(condition_id, underage, source_handle=false_h)

workflow.save("age_check.json")
```

## 输出格式

生成的 JSON 包含以下关键部分:

```json
{
  "created_by": "Claude Agent SDK",
  "flow_uuid": "...",
  "flow_name": "...",
  "nodes": [
    // 功能节点（hidden: true）
    // Block 节点（visible）
  ],
  "edges": [
    // 节点之间的连接
  ],
  "variables": [
    // 变量定义
  ]
}
```

## 节点结构规范

### 功能节点
- `hidden`: true
- `position`: `{x: 125, y: 递增}`
- `blockId`: 指向对应的 block

### Block 节点
- `hidden`: false (可见)
- `position`: `{x: 递增, y: offset}`
- `include_node_ids`: 包含的功能节点 ID

## 位置计算规则

- **功能节点**: 固定 `x=125`, y 从 325 开始每次 +200
- **Block 节点**: x 从 475 开始每次 +350, y = functional_y - 50

## 关键 API

### NaturalLanguageParser

```python
from src.parsers.nl_parser import NaturalLanguageParser

parser = NaturalLanguageParser()
workflow = parser.parse(description, workflow_name, workflow_description)
```

### Workflow 类

```python
from src.core.workflow import Workflow

wf = Workflow("name", "description")
wf.add_text_reply(message, title)
wf.add_capture_user_reply(variable_name, title)
wf.add_condition(var, value, label, title, operator)
wf.add_code_node(code, outputs, inputs, title)
wf.connect_nodes(source, target, source_handle, target_handle)
wf.save(filepath)
```

## 最佳实践

1. **使用 NaturalLanguageParser**: 对于简单的线性流程，直接使用解析器
2. **手动构建复杂流程**: 对于复杂的分支和循环，手动使用 Workflow API
3. **验证生成结果**: 检查节点数、边数和变量数
4. **测试 JSON**: 确保生成的 JSON 可以被工作流引擎加载

## 命令行工具

```bash
# 基本用法
python -m src.cli "自然语言描述"

# 指定输出和名称
python -m src.cli "描述" -o output.json -n workflow_name

# 从文件读取
python -m src.cli input.txt -o output.json

# 详细输出
python -m src.cli "描述" --verbose
```

## 总结

这个工作流生成器提供了一个简单但强大的方式，将自然语言描述转换为结构化的工作流配置。通过 NaturalLanguageParser 和 Workflow API，你可以快速生成符合规范的工作流 JSON 文件。
