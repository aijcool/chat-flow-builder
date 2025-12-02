"""
节点生成模块 - 生成所有类型的 chatflow 节点
"""
from typing import Dict, List, Optional, Any
from ..utils.id_generator import generate_uuid, generate_start_node_id


# ============ 基础节点生成器 ============

def create_start_node(
    position_x: int = 125,
    position_y: int = 325,
    source_handle: Optional[str] = None
) -> Dict:
    """
    创建 Start 节点 (工作流入口点)

    Args:
        position_x: X 坐标 (默认: 125)
        position_y: Y 坐标 (默认: 325)
        source_handle: 源句柄 ID (可选,默认自动生成)

    Returns:
        dict: Start 节点配置
    """
    if source_handle is None:
        source_handle = generate_uuid()

    return {
        "id": generate_start_node_id(),
        "type": "start",
        "initialized": False,
        "position": {
            "x": position_x,
            "y": position_y
        },
        "data": {
            "label": "Start",
            "showToolBar": False,
            "targetPosition": "left",
            "sourcePosition": "right",
            "sourceHandle": source_handle
        }
    }


def create_text_reply_node(
    text: str,
    title: str = "Response",
    node_id: Optional[str] = None,
    block_id: Optional[str] = None,
    position_x: int = 125,
    position_y: int = 525,
    async_run: bool = False
) -> Dict:
    """
    创建 textReply 节点 (发送文本消息)

    Args:
        text: 要发送的文本内容
        title: 节点标题 (默认: "Response")
        node_id: 节点 ID (可选,默认自动生成)
        block_id: 关联的 Block ID (必须提供或自动生成)
        position_x: X 坐标 (默认: 125)
        position_y: Y 坐标 (默认: 525)
        async_run: 是否异步运行 (默认: False)

    Returns:
        dict: textReply 节点配置
    """
    if node_id is None:
        node_id = generate_uuid()
    if block_id is None:
        block_id = generate_uuid()

    source_handle = generate_uuid()
    text_id = generate_uuid()

    return {
        "id": node_id,
        "type": "textReply",
        "initialized": False,
        "position": {
            "x": position_x,
            "y": position_y
        },
        "data": {
            "sourceHandle": source_handle,
            "showToolBar": False,
            "targetPosition": "left",
            "sourcePosition": "right"
        },
        "blockId": block_id,
        "hidden": True,
        "config": {
            "async_run": async_run,
            "plain_text": [
                {
                    "text": text,
                    "id": text_id
                }
            ],
            "rich_text": [],
            "title": title
        }
    }


def create_capture_user_reply_node(
    variable_name: str,
    title: str = "Capture",
    node_id: Optional[str] = None,
    block_id: Optional[str] = None,
    position_x: int = 125,
    position_y: int = 725
) -> Dict:
    """
    创建 captureUserReply 节点 (捕获用户输入)

    Args:
        variable_name: 保存用户输入的变量名
        title: 节点标题 (默认: "Capture")
        node_id: 节点 ID (可选,默认自动生成)
        block_id: 关联的 Block ID (必须提供或自动生成)
        position_x: X 坐标 (默认: 125)
        position_y: Y 坐标 (默认: 725)

    Returns:
        dict: captureUserReply 节点配置
    """
    if node_id is None:
        node_id = generate_uuid()
    if block_id is None:
        block_id = generate_uuid()

    source_handle = generate_uuid()

    return {
        "id": node_id,
        "type": "captureUserReply",
        "initialized": False,
        "position": {
            "x": position_x,
            "y": position_y
        },
        "data": {
            "sourceHandle": source_handle,
            "showToolBar": False,
            "targetPosition": "left",
            "sourcePosition": "right"
        },
        "blockId": block_id,
        "hidden": True,
        "config": {
            "variable_assign": variable_name,
            "title": title
        }
    }


# ============ 逻辑节点生成器 ============

def create_condition_node(
    if_else_conditions: List[Dict],
    title: str = "Condition",
    node_id: Optional[str] = None,
    block_id: Optional[str] = None,
    position_x: int = 125,
    position_y: int = 925
) -> Dict:
    """
    创建 condition 节点 (条件分支)

    Args:
        if_else_conditions: 条件分支列表,格式:
            [
                {
                    "condition_id": "uuid",  # 可选,默认自动生成
                    "condition_name": "条件名称",
                    "logical_operator": "and",
                    "conditions": [
                        {
                            "condition_type": "variable",
                            "comparison_operator": "=",
                            "condition_value": "1",
                            "condition_variable": "result"
                        }
                    ],
                    "condition_action": []
                },
                ...
            ]
        title: 节点标题 (默认: "Condition")
        node_id: 节点 ID (可选,默认自动生成)
        block_id: 关联的 Block ID (必须提供或自动生成)
        position_x: X 坐标
        position_y: Y 坐标

    Returns:
        dict: condition 节点配置
    """
    if node_id is None:
        node_id = generate_uuid()
    if block_id is None:
        block_id = generate_uuid()

    source_handle = generate_uuid()

    # 确保每个条件都有 condition_id
    for cond in if_else_conditions:
        if "condition_id" not in cond or cond["condition_id"] is None:
            cond["condition_id"] = generate_uuid()

    return {
        "id": node_id,
        "type": "condition",
        "initialized": False,
        "position": {
            "x": position_x,
            "y": position_y
        },
        "data": {
            "sourceHandle": source_handle,
            "showToolBar": False,
            "targetPosition": "left",
            "sourcePosition": "right"
        },
        "blockId": block_id,
        "hidden": True,
        "config": {
            "if_else_conditions": if_else_conditions,
            "title": title
        }
    }


# ============ 代码执行节点生成器 ============

def create_code_node(
    code: str,
    outputs: List[Dict],
    args: Optional[List[Dict]] = None,
    title: str = "Code",
    description: str = "",
    code_language: str = "python3",
    node_id: Optional[str] = None,
    block_id: Optional[str] = None,
    position_x: int = 125,
    position_y: int = 1125
) -> Dict:
    """
    创建 code 节点 (Python 代码执行)

    Args:
        code: Python 代码字符串
        outputs: 输出变量列表,格式:
            [
                {
                    "name": "result",
                    "type": "string",
                    "variable_assign": "result"
                }
            ]
        args: 输入参数列表 (可选),格式:
            [
                {
                    "name": "input_var",
                    "default_value": "{{variable_name}}",
                    "type": "string"
                }
            ]
        title: 节点标题 (默认: "Code")
        description: 节点描述 (默认: "")
        code_language: 代码语言 (默认: "python3")
        node_id: 节点 ID (可选,默认自动生成)
        block_id: 关联的 Block ID (必须提供或自动生成)
        position_x: X 坐标
        position_y: Y 坐标

    Returns:
        dict: code 节点配置
    """
    if node_id is None:
        node_id = generate_uuid()
    if block_id is None:
        block_id = generate_uuid()
    if args is None:
        args = []

    source_handle = generate_uuid()

    return {
        "id": node_id,
        "type": "code",
        "initialized": False,
        "position": {
            "x": position_x,
            "y": position_y
        },
        "data": {
            "sourceHandle": source_handle,
            "showToolBar": False,
            "targetPosition": "left",
            "sourcePosition": "right"
        },
        "blockId": block_id,
        "hidden": True,
        "config": {
            "title": title,
            "desc": description,
            "code": code,
            "code_language": code_language,
            "outputs": outputs,
            "args": args
        }
    }


# ============ LLM 节点生成器 ============

def create_llm_variable_assignment_node(
    prompt_template: str,
    variable_assign: str,
    llm_config: Optional[Dict] = None,
    title: str = "LLM Assignment",
    description: str = "",
    node_id: Optional[str] = None,
    block_id: Optional[str] = None,
    position_x: int = 125,
    position_y: int = 1325
) -> Dict:
    """
    创建 llmVariableAssignment 节点 (LLM 提取并赋值变量)

    Args:
        prompt_template: Prompt 模板 (用户输入部分)
        variable_assign: 要赋值的变量名
        llm_config: LLM 配置 (可选),默认使用标准配置
        title: 节点标题 (默认: "LLM Assignment")
        description: 节点描述 (默认: "")
        node_id: 节点 ID (可选,默认自动生成)
        block_id: 关联的 Block ID (必须提供或自动生成)
        position_x: X 坐标
        position_y: Y 坐标

    Returns:
        dict: llmVariableAssignment 节点配置
    """
    if node_id is None:
        node_id = generate_uuid()
    if block_id is None:
        block_id = generate_uuid()

    source_handle = generate_uuid()

    # 默认 LLM 配置
    if llm_config is None:
        llm_config = {
            "rag_correlation_threshold": 65,
            "rag_max_reference_knowledge_num": 3,
            "divergence": 2,
            "prompt": "",  # System prompt (可选)
            "llm_name": "azure-gpt-4o",
            "rag_question": "",
            "rag_range": "",
            "rag_enabled": "",
            "knowledge_base_ids": [],
            "knowledge_search_flag": False,
            "chat_history_flag": False,
            "chat_history_count": 5,
            "ltm_enabled": False,
            "ltm_search_range": "0",
            "ltm_robot_ids": [],
            "ltm_question": "",
            "ltm_recall_count": 5
        }

    return {
        "id": node_id,
        "type": "llmVariableAssignment",
        "initialized": False,
        "position": {
            "x": position_x,
            "y": position_y
        },
        "data": {
            "sourceHandle": source_handle,
            "showToolBar": False,
            "targetPosition": "left",
            "sourcePosition": "right"
        },
        "blockId": block_id,
        "hidden": True,
        "config": {
            "title": title,
            "desc": description,
            "prompt_template": prompt_template,
            "variable_assign": variable_assign,
            "llm_config": llm_config
        }
    }


def create_llm_reply_node(
    prompt_template: str,
    llm_config: Optional[Dict] = None,
    title: str = "LLM Reply",
    description: str = "",
    async_run: bool = False,
    node_id: Optional[str] = None,
    block_id: Optional[str] = None,
    position_x: int = 125,
    position_y: int = 1525
) -> Dict:
    """
    创建 llMReply 节点 (LLM 直接回复用户)

    Args:
        prompt_template: Prompt 模板
        llm_config: LLM 配置 (可选),默认使用标准配置
        title: 节点标题 (默认: "LLM Reply")
        description: 节点描述 (默认: "")
        async_run: 是否异步运行 (默认: False)
        node_id: 节点 ID (可选,默认自动生成)
        block_id: 关联的 Block ID (必须提供或自动生成)
        position_x: X 坐标
        position_y: Y 坐标

    Returns:
        dict: llMReply 节点配置
    """
    if node_id is None:
        node_id = generate_uuid()
    if block_id is None:
        block_id = generate_uuid()

    source_handle = generate_uuid()

    # 默认 LLM 配置 (包含额外的 llMReply 特定字段)
    if llm_config is None:
        llm_config = {
            "rag_correlation_threshold": 65,
            "rag_max_reference_knowledge_num": 3,
            "slang_enable": False,
            "divergence": 2,
            "prompt": "",  # System prompt
            "llm_name": "azure-gpt-4o",
            "rag_question": "",
            "rag_range": "",
            "rag_enabled": "",
            "knowledge_base_ids": [],
            "knowledge_search_flag": False,
            "chat_history_flag": True,  # 默认启用对话历史
            "chat_history_count": 5,
            "ltm_enabled": False,
            "ltm_search_range": "0",
            "ltm_robot_ids": [],
            "ltm_question": "",
            "ltm_recall_count": 5,
            "verify_enable": False,
            "verify_count": 5,
            "verify_constraints": "",
            "main_condition_id": generate_uuid(),
            "other_condition_id": generate_uuid()
        }

    return {
        "id": node_id,
        "type": "llMReply",
        "initialized": False,
        "position": {
            "x": position_x,
            "y": position_y
        },
        "data": {
            "sourceHandle": source_handle,
            "showToolBar": False,
            "targetPosition": "left",
            "sourcePosition": "right"
        },
        "blockId": block_id,
        "hidden": True,
        "config": {
            "desc": description,
            "prompt_template": prompt_template,
            "async_run": async_run,
            "llm_config": llm_config,
            "title": title
        }
    }


# ============ 节点生成器类 ============

class NodeGenerator:
    """节点生成器类 - 批量管理节点生成"""

    def __init__(self):
        """初始化节点生成器"""
        self.nodes: List[Dict] = []

    def add_start_node(
        self,
        position_x: int = 125,
        position_y: int = 325
    ) -> Dict:
        """
        添加 Start 节点

        Args:
            position_x: X 坐标
            position_y: Y 坐标

        Returns:
            dict: 生成的 Start 节点
        """
        node = create_start_node(position_x, position_y)
        self.nodes.append(node)
        return node

    def add_text_reply(
        self,
        text: str,
        title: str = "Response",
        position_x: int = 125,
        position_y: int = 525,
        block_id: Optional[str] = None
    ) -> Dict:
        """
        添加 textReply 节点

        Args:
            text: 文本内容
            title: 节点标题
            position_x: X 坐标
            position_y: Y 坐标
            block_id: Block ID (可选)

        Returns:
            dict: 生成的 textReply 节点
        """
        node = create_text_reply_node(
            text=text,
            title=title,
            position_x=position_x,
            position_y=position_y,
            block_id=block_id
        )
        self.nodes.append(node)
        return node

    def add_capture_user_reply(
        self,
        variable_name: str,
        title: str = "Capture",
        position_x: int = 125,
        position_y: int = 725,
        block_id: Optional[str] = None
    ) -> Dict:
        """
        添加 captureUserReply 节点

        Args:
            variable_name: 变量名
            title: 节点标题
            position_x: X 坐标
            position_y: Y 坐标
            block_id: Block ID (可选)

        Returns:
            dict: 生成的 captureUserReply 节点
        """
        node = create_capture_user_reply_node(
            variable_name=variable_name,
            title=title,
            position_x=position_x,
            position_y=position_y,
            block_id=block_id
        )
        self.nodes.append(node)
        return node

    def add_condition(
        self,
        if_else_conditions: List[Dict],
        title: str = "Condition",
        position_x: int = 125,
        position_y: int = 925,
        block_id: Optional[str] = None
    ) -> Dict:
        """
        添加 condition 节点

        Args:
            if_else_conditions: 条件分支列表
            title: 节点标题
            position_x: X 坐标
            position_y: Y 坐标
            block_id: Block ID (可选)

        Returns:
            dict: 生成的 condition 节点
        """
        node = create_condition_node(
            if_else_conditions=if_else_conditions,
            title=title,
            position_x=position_x,
            position_y=position_y,
            block_id=block_id
        )
        self.nodes.append(node)
        return node

    def add_code(
        self,
        code: str,
        outputs: List[Dict],
        args: Optional[List[Dict]] = None,
        title: str = "Code",
        position_x: int = 125,
        position_y: int = 1125,
        block_id: Optional[str] = None
    ) -> Dict:
        """
        添加 code 节点

        Args:
            code: Python 代码
            outputs: 输出变量列表
            args: 输入参数列表 (可选)
            title: 节点标题
            position_x: X 坐标
            position_y: Y 坐标
            block_id: Block ID (可选)

        Returns:
            dict: 生成的 code 节点
        """
        node = create_code_node(
            code=code,
            outputs=outputs,
            args=args,
            title=title,
            position_x=position_x,
            position_y=position_y,
            block_id=block_id
        )
        self.nodes.append(node)
        return node

    def add_llm_variable_assignment(
        self,
        prompt_template: str,
        variable_assign: str,
        llm_config: Optional[Dict] = None,
        title: str = "LLM Assignment",
        position_x: int = 125,
        position_y: int = 1325,
        block_id: Optional[str] = None
    ) -> Dict:
        """
        添加 llmVariableAssignment 节点

        Args:
            prompt_template: Prompt 模板
            variable_assign: 要赋值的变量名
            llm_config: LLM 配置 (可选)
            title: 节点标题
            position_x: X 坐标
            position_y: Y 坐标
            block_id: Block ID (可选)

        Returns:
            dict: 生成的 llmVariableAssignment 节点
        """
        node = create_llm_variable_assignment_node(
            prompt_template=prompt_template,
            variable_assign=variable_assign,
            llm_config=llm_config,
            title=title,
            position_x=position_x,
            position_y=position_y,
            block_id=block_id
        )
        self.nodes.append(node)
        return node

    def add_llm_reply(
        self,
        prompt_template: str,
        llm_config: Optional[Dict] = None,
        title: str = "LLM Reply",
        position_x: int = 125,
        position_y: int = 1525,
        block_id: Optional[str] = None
    ) -> Dict:
        """
        添加 llMReply 节点

        Args:
            prompt_template: Prompt 模板
            llm_config: LLM 配置 (可选)
            title: 节点标题
            position_x: X 坐标
            position_y: Y 坐标
            block_id: Block ID (可选)

        Returns:
            dict: 生成的 llMReply 节点
        """
        node = create_llm_reply_node(
            prompt_template=prompt_template,
            llm_config=llm_config,
            title=title,
            position_x=position_x,
            position_y=position_y,
            block_id=block_id
        )
        self.nodes.append(node)
        return node

    def get_all_nodes(self) -> List[Dict]:
        """
        获取所有生成的节点

        Returns:
            list: 节点列表
        """
        return self.nodes

    def count(self) -> int:
        """
        获取节点数量

        Returns:
            int: 节点数量
        """
        return len(self.nodes)

    def clear(self):
        """清除所有节点"""
        self.nodes.clear()

    def __len__(self) -> int:
        """支持 len() 函数"""
        return len(self.nodes)

    def __repr__(self):
        return f"NodeGenerator(nodes_count={len(self.nodes)})"
