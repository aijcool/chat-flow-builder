"""
Chatflow Agent - 使用 Claude Agent SDK 模式构建的对话式工作流生成 Agent

基于官方 Claude Agent SDK 文档实现:
https://platform.claude.com/docs/en/agent-sdk/python

核心模式:
1. Agentic Loop - 通过检查 response.stop_reason 实现工具调用循环
2. 工具定义 - 使用 JSON Schema 定义工具
3. 消息历史管理 - 正确维护对话上下文
"""
import json
from typing import List, Dict, Optional, Any, Callable
from anthropic import Anthropic
from .tools import TOOLS, execute_tool

# 进度回调类型: (event_type: str, data: dict) -> None
ProgressCallback = Callable[[str, Dict[str, Any]], None]


class ChatflowAgent:
    """
    Chatflow 生成 Agent - 使用 Claude Agent SDK 模式

    功能:
    - 对话式理解用户需求
    - 通过 agentic loop 自动执行工具调用
    - 提供友好的交互体验
    """

    # 系统提示词
    SYSTEM_PROMPT = """你是一个专业的 Chatflow 生成助手,帮助用户将自然语言描述转换为 Agent Studio 的 chatflow JSON 文件。

你的职责:
1. 理解用户的需求 - 深入分析用户想要创建什么样的对话流程
2. 直接生成 - 根据用户描述直接构造完整的步骤数组
3. 提供反馈 - 清晰地告知用户生成结果

## 创建新工作流流程:
1. 用户描述需求
2. 你根据描述的复杂度,自行决定工作流名称,并构造完整的 steps 数组
3. 直接调用 generate_workflow 工具（该工具会自动保存到 Supabase）
4. 告知用户完成情况

【重要】不要使用 parse_workflow_description 工具！你应该自己理解用户需求并直接构造 steps 数组。

## 节点类型和格式:
- textReply: {"type": "textReply", "text": "消息内容", "title": "节点标题"}
- captureUserReply: {"type": "captureUserReply", "variable": "变量名", "title": "节点标题"}
- llmVariableAssignment: {"type": "llmVariableAssignment", "prompt": "提示词模板,使用{{变量名}}引用变量", "variable": "目标变量", "title": "节点标题"}
- condition: {"type": "condition", "variable": "要判断的变量名", "operator": "=", "value": "期望值", "condition_name": "条件名称", "title": "节点标题"}
- llMReply: {"type": "llMReply", "prompt": "提示词模板", "title": "节点标题"}
- code: {"type": "code", "code": "代码内容", "title": "节点标题"}

## 【核心设计模式 - 必须严格遵循】

### 模式1: 用户输入处理三连
每次收集用户输入时,必须按以下顺序生成3个节点:
1. captureUserReply - 收集原始输入到变量 (如 raw_input)
2. llmVariableAssignment - 立即用LLM提取/验证信息 (如 extracted_data)
3. condition - 基于提取结果进行判断

示例:
```
{"type": "textReply", "text": "请输入您的出发城市", "title": "询问出发城市"}
{"type": "captureUserReply", "variable": "departure_raw", "title": "收集出发城市"}
{"type": "llmVariableAssignment", "prompt": "从用户输入'{{departure_raw}}'中提取城市名称。如果是有效城市名返回城市名,否则返回'invalid'", "variable": "departure_city", "title": "提取出发城市"}
{"type": "condition", "variable": "departure_city", "operator": "!=", "value": "invalid", "condition_name": "城市有效", "title": "验证出发城市"}
```

### 模式2: 条件判断必须有完整分支
每个 condition 节点后必须处理两种情况:
- 条件满足: 继续正常流程
- 条件不满足:
  - 使用 llMReply 智能提示用户错误原因
  - 或者使用 textReply 提示重新输入
  - 然后循环回到收集信息的节点(在实际连线时处理)

### 模式3: 验证提示词格式
llmVariableAssignment 的 prompt 必须:
- 使用 {{变量名}} 格式引用之前的变量
- 明确指定有效/无效的返回值格式
- 示例: "分析{{user_input}},如果包含有效日期返回'YYYY-MM-DD'格式,否则返回'invalid'"

## 完整流程示例 (机票预订):
```
1. textReply: "欢迎使用机票预订服务！请输入出发城市"
2. captureUserReply: departure_raw
3. llmVariableAssignment: 从{{departure_raw}}提取城市 -> departure_city
4. condition: departure_city != "invalid"
5. textReply (条件不满足时): "抱歉,未能识别城市名,请重新输入"
6. textReply (条件满足时): "请输入目的城市"
7. captureUserReply: destination_raw
8. llmVariableAssignment: 从{{destination_raw}}提取城市 -> destination_city
9. condition: destination_city != "invalid"
...以此类推
```

## 注意事项:
- 【禁止】captureUserReply 后直接接 condition,必须先用 llmVariableAssignment 提取
- 【禁止】condition 的 variable 使用原始输入变量,必须使用 LLM 提取后的变量
- 【必须】每个验证失败的分支都要有提示信息
- 当工作流生成成功后,回复只需包含: 成功提示 + [文件名.json] + 简短描述"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        user_id: str = "public"
    ):
        """
        初始化 Agent

        Args:
            api_key: Anthropic API Key
            base_url: API Base URL (可选,用于兼容 API)
            model: 模型名称
            user_id: 用户 ID (用于存储工作流)
        """
        self.model = model
        self.user_id = user_id

        # 初始化 Anthropic 客户端
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = Anthropic(**client_kwargs)

        # 对话历史 (按照 SDK 模式维护)
        self.messages: List[Dict[str, Any]] = []

        # 进度回调函数 (用于 SSE 推送)
        self._progress_callback: Optional[ProgressCallback] = None

    def set_progress_callback(self, callback: Optional[ProgressCallback]):
        """设置进度回调函数"""
        self._progress_callback = callback

    def _emit_progress(self, event_type: str, data: Dict[str, Any]):
        """发送进度事件"""
        if self._progress_callback:
            try:
                self._progress_callback(event_type, data)
            except Exception as e:
                print(f"[进度回调错误] {e}")

    def _process_tool_call(self, tool_name: str, tool_input: Dict) -> str:
        """
        处理工具调用

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数

        Returns:
            str: 工具执行结果 (JSON 字符串，已简化，不含完整 workflow)
        """
        # 自动注入 user_id 到需要的工具
        tools_needing_user_id = [
            "generate_workflow",
            "save_workflow_to_file",
            "list_workflow_files",
            "load_workflow_file"
        ]
        if tool_name in tools_needing_user_id and "user_id" not in tool_input:
            tool_input["user_id"] = self.user_id

        print(f"\n[调用工具] {tool_name}")
        print(f"[输入参数] {json.dumps(tool_input, ensure_ascii=False, indent=2)}")

        # 发送工具调用进度事件
        self._emit_progress("tool", {
            "name": tool_name,
            "status": "calling",
            "message": f"调用工具: {tool_name}"
        })

        # 执行工具
        result = execute_tool(tool_name, tool_input)

        print(f"[执行结果] {result.get('message', 'OK')}")

        # 发送工具完成事件
        self._emit_progress("tool", {
            "name": tool_name,
            "status": "completed",
            "message": result.get('message', 'OK'),
            "success": result.get('success', True)
        })

        # 简化返回给 Claude 的结果，移除大型数据
        # 只保留必要的元信息，完整数据已保存到 Supabase
        simplified_result = {
            "success": result.get("success", True),
            "message": result.get("message", "OK")
        }

        # 保留关键字段（但不包含完整 workflow）
        for key in ["filename", "storage_url", "storage_path", "stats", "count", "files", "summary"]:
            if key in result:
                # files 列表也简化，只保留文件名
                if key == "files" and isinstance(result[key], list):
                    simplified_result[key] = [{"name": f.get("name")} for f in result[key]]
                else:
                    simplified_result[key] = result[key]

        return json.dumps(simplified_result, ensure_ascii=False)

    def _run_agentic_loop(self) -> str:
        """
        运行 Agentic Loop - Claude Agent SDK 核心模式

        循环执行直到 Claude 返回 end_turn (不再需要工具调用)

        Returns:
            str: 最终的助手回复文本
        """
        loop_count = 0
        while True:
            loop_count += 1

            # 发送进度: 调用 LLM
            self._emit_progress("progress", {
                "status": "thinking",
                "message": f"AI 思考中... (第 {loop_count} 轮)",
                "loop": loop_count
            })

            # 调用 Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=self.SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.messages
            )

            # 检查停止原因 (Claude Agent SDK 核心模式)
            if response.stop_reason == "end_turn":
                # Claude 完成了回复,不需要更多工具调用
                # 提取文本内容
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text

                # 将最终回复添加到消息历史
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # 发送完成进度
                self._emit_progress("progress", {
                    "status": "completed",
                    "message": "处理完成",
                    "loop": loop_count
                })

                return final_text

            elif response.stop_reason == "tool_use":
                # Claude 请求使用工具
                # 1. 将助手的响应 (包含 tool_use) 添加到消息历史
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # 2. 处理所有工具调用并收集结果
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_result = self._process_tool_call(
                            tool_name=block.name,
                            tool_input=block.input
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result
                        })

                # 3. 将工具结果添加到消息历史
                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # 继续循环,让 Claude 处理工具结果

            else:
                # 其他停止原因 (如 max_tokens)
                print(f"[警告] 意外的停止原因: {response.stop_reason}")
                self._emit_progress("progress", {
                    "status": "warning",
                    "message": f"意外的停止原因: {response.stop_reason}"
                })
                # 尝试提取已有的文本内容
                text_content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text_content += block.text
                return text_content if text_content else "处理过程中发生错误"

    def chat(self, user_message: str) -> str:
        """
        发送用户消息并获取 Agent 回复

        Args:
            user_message: 用户消息

        Returns:
            str: Agent 回复
        """
        # 添加用户消息到历史
        self.messages.append({
            "role": "user",
            "content": user_message
        })

        # 运行 agentic loop
        return self._run_agentic_loop()

    def quick_generate(
        self,
        description: str,
        workflow_name: str,
        lang: str = "auto"
    ) -> Dict:
        """
        快速生成 workflow (单轮,非对话式)

        Args:
            description: 自然语言描述
            workflow_name: 工作流名称
            lang: 语言 (auto, zh, en)

        Returns:
            dict: 生成结果
        """
        # 1. 解析描述
        parse_result = execute_tool("parse_workflow_description", {
            "description": description,
            "lang": lang
        })

        if not parse_result.get("success", True):
            return parse_result

        # 2. 生成 workflow
        generate_result = execute_tool("generate_workflow", {
            "workflow_name": workflow_name,
            "steps": parse_result["steps"],
            "description": description,
            "lang": "zh" if lang == "zh" else "en"
        })

        if not generate_result.get("success"):
            return generate_result

        # 3. 保存文件
        save_result = execute_tool("save_workflow_to_file", {
            "workflow": generate_result["workflow"],
            "filename": workflow_name
        })

        return {
            "success": save_result["success"],
            "filepath": save_result.get("filepath"),
            "stats": generate_result["stats"],
            "message": f"成功生成 {workflow_name},保存到 {save_result.get('filepath')}"
        }

    def reset_conversation(self):
        """重置对话历史"""
        self.messages.clear()

    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.messages

    def __repr__(self):
        return f"ChatflowAgent(model='{self.model}', messages={len(self.messages)})"


def run_agent_interactive(api_key: str, base_url: Optional[str] = None):
    """
    交互式运行 Agent

    Args:
        api_key: Anthropic API Key
        base_url: API Base URL (可选)
    """
    agent = ChatflowAgent(api_key=api_key, base_url=base_url)

    print("=" * 60)
    print("Chatflow Agent - 使用 Claude Agent SDK 模式")
    print("=" * 60)
    print("输入您的需求,我会帮您生成 Agent Studio chatflow JSON 文件")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'reset' 重置对话")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n您: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit"]:
                print("再见!")
                break

            if user_input.lower() == "reset":
                agent.reset_conversation()
                print("[对话已重置]")
                continue

            # 获取 Agent 回复
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")

        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except Exception as e:
            print(f"\n[错误] {e}")


# 命令行入口
if __name__ == "__main__":
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("请设置 ANTHROPIC_API_KEY 环境变量")
        exit(1)

    run_agent_interactive(api_key)
