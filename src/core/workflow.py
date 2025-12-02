"""
Workflow 构建器模块 - 编排所有组件生成完整的 chatflow JSON
"""
import json
from typing import Dict, List, Optional, Tuple
from ..utils.id_generator import generate_uuid, generate_start_node_id
from ..utils.position_calc import PositionCalculator
from ..core.variables import VariableTracker
from ..core.edges import EdgeManager
from ..generators.node_generator import (
    create_start_node,
    create_text_reply_node,
    create_capture_user_reply_node,
    create_condition_node,
    create_code_node,
    create_llm_variable_assignment_node,
    create_llm_reply_node
)
from ..generators.block_generator import create_block_for_functional_node


class Workflow:
    """
    Workflow 构建器类 - 管理整个 chatflow 的生成

    功能:
    - 自动管理节点和 Block 的生成
    - 自动计算节点位置
    - 自动注册变量
    - 管理边连接
    - 导出完整 JSON
    """

    def __init__(
        self,
        flow_name: str,
        description: str = "",
        lang: str = "en",
        created_by: str = "Claude Agent SDK",
        modified_by: str = "Claude Agent SDK"
    ):
        """
        初始化 Workflow

        Args:
            flow_name: 工作流名称
            description: 工作流描述 (可选)
            lang: 语言代码 (默认: "en")
            created_by: 创建者 (默认: "Claude Agent SDK")
            modified_by: 修改者 (默认: "Claude Agent SDK")
        """
        self.flow_name = flow_name
        self.description = description
        self.lang = lang
        self.created_by = created_by
        self.modified_by = modified_by

        # 核心组件
        self.position_calc = PositionCalculator()
        self.variable_tracker = VariableTracker(lang=lang)
        self.edge_manager = EdgeManager()

        # 节点存储
        self.nodes: List[Dict] = []
        self.start_node: Optional[Dict] = None

        # UUID 存储
        self.flow_uuid = generate_uuid()
        self.intention_uuid = generate_uuid()

        # 前一个节点 ID (用于自动连接)
        self.last_block_id: Optional[str] = None

        # 节点 handle 映射 (node_id -> sourceHandle)
        self.node_handles: Dict[str, str] = {}

        # Block 到功能节点的映射 (block_id -> functional_node_id)
        self.block_to_func: Dict[str, str] = {}

        # 功能节点到 Block 的映射 (functional_node_id -> block_id)
        self.func_to_block: Dict[str, str] = {}

    # ============ 节点添加方法 ============

    def add_start_node(self) -> str:
        """
        添加 Start 节点 (每个 workflow 只能有一个)

        Returns:
            str: Start 节点的 ID
        """
        if self.start_node is not None:
            raise ValueError("Start node already exists. Only one start node is allowed per workflow.")

        position = self.position_calc.get_start_position()
        self.start_node = create_start_node(
            position_x=position["x"],
            position_y=position["y"]
        )
        self.nodes.append(self.start_node)
        self.last_block_id = self.start_node["id"]

        # 存储 start 节点的 sourceHandle
        self.node_handles[self.start_node["id"]] = self.start_node["data"]["sourceHandle"]

        return self.start_node["id"]

    def add_text_reply(
        self,
        text: str,
        title: str = "Response",
        auto_connect: bool = True
    ) -> str:
        """
        添加 textReply 节点 + Block 包装器

        Args:
            text: 文本内容
            title: 节点标题 (默认: "Response")
            auto_connect: 是否自动连接到前一个节点 (默认: True)

        Returns:
            str: Block 节点的 ID
        """
        # 生成位置
        functional_pos, block_pos = self.position_calc.get_node_pair_positions()

        # 生成 Block ID
        block_id = generate_uuid()

        # 创建功能节点
        functional_node = create_text_reply_node(
            text=text,
            title=title,
            block_id=block_id,
            position_x=functional_pos["x"],
            position_y=functional_pos["y"]
        )

        # 创建 Block 包装器
        block_node = create_block_for_functional_node(
            functional_node_id=functional_node["id"],
            label=title,
            block_position=block_pos,
            block_id=block_id
        )

        # 添加到节点列表
        self.nodes.append(functional_node)
        self.nodes.append(block_node)

        # 存储 sourceHandle - 使用功能节点的 data.sourceHandle
        self.node_handles[block_id] = functional_node["data"]["sourceHandle"]

        # 存储双向映射
        self.block_to_func[block_id] = functional_node["id"]
        self.func_to_block[functional_node["id"]] = block_id

        # 自动连接
        if auto_connect and self.last_block_id:
            self.connect_nodes(self.last_block_id, block_id)

        self.last_block_id = block_id
        return block_id

    def add_capture_user_reply(
        self,
        variable_name: str,
        description: Optional[str] = None,
        title: str = "Capture",
        auto_connect: bool = True
    ) -> str:
        """
        添加 captureUserReply 节点 + Block 包装器

        Args:
            variable_name: 变量名
            description: 变量描述 (可选,默认使用变量名)
            title: 节点标题 (默认: "Capture")
            auto_connect: 是否自动连接到前一个节点 (默认: True)

        Returns:
            str: Block 节点的 ID
        """
        # 注册变量
        self.variable_tracker.register(variable_name, description)

        # 生成位置
        functional_pos, block_pos = self.position_calc.get_node_pair_positions()

        # 生成 Block ID
        block_id = generate_uuid()

        # 创建功能节点
        functional_node = create_capture_user_reply_node(
            variable_name=variable_name,
            title=title,
            block_id=block_id,
            position_x=functional_pos["x"],
            position_y=functional_pos["y"]
        )

        # 创建 Block 包装器
        block_node = create_block_for_functional_node(
            functional_node_id=functional_node["id"],
            label=title,
            block_position=block_pos,
            block_id=block_id
        )

        # 添加到节点列表
        self.nodes.append(functional_node)
        self.nodes.append(block_node)

        # 存储 sourceHandle - 使用功能节点的 data.sourceHandle
        self.node_handles[block_id] = functional_node["data"]["sourceHandle"]

        # 存储双向映射
        self.block_to_func[block_id] = functional_node["id"]
        self.func_to_block[functional_node["id"]] = block_id

        # 自动连接
        if auto_connect and self.last_block_id:
            self.connect_nodes(self.last_block_id, block_id)

        self.last_block_id = block_id
        return block_id

    def add_condition(
        self,
        if_else_conditions: List[Dict],
        title: str = "Condition",
        auto_connect: bool = True
    ) -> Tuple[str, List[str]]:
        """
        添加 condition 节点 + Block 包装器

        Args:
            if_else_conditions: 条件分支列表 (每个条件会自动生成 condition_id)
            title: 节点标题 (默认: "Condition")
            auto_connect: 是否自动连接到前一个节点 (默认: True)

        Returns:
            tuple: (block_id, [condition_id1, condition_id2, ...])
        """
        # 生成位置
        functional_pos, block_pos = self.position_calc.get_node_pair_positions()

        # 生成 Block ID
        block_id = generate_uuid()

        # 创建功能节点 (会自动为每个条件生成 condition_id)
        functional_node = create_condition_node(
            if_else_conditions=if_else_conditions,
            title=title,
            block_id=block_id,
            position_x=functional_pos["x"],
            position_y=functional_pos["y"]
        )

        # 创建 Block 包装器
        block_node = create_block_for_functional_node(
            functional_node_id=functional_node["id"],
            label=title,
            block_position=block_pos,
            block_id=block_id
        )

        # 添加到节点列表
        self.nodes.append(functional_node)
        self.nodes.append(block_node)

        # 存储双向映射
        self.block_to_func[block_id] = functional_node["id"]
        self.func_to_block[functional_node["id"]] = block_id

        # 自动连接
        if auto_connect and self.last_block_id:
            self.connect_nodes(self.last_block_id, block_id)

        # 提取所有 condition_id
        condition_ids = [cond["condition_id"] for cond in functional_node["config"]["if_else_conditions"]]

        self.last_block_id = block_id
        return block_id, condition_ids

    def add_code(
        self,
        code: str,
        outputs: List[Dict],
        args: Optional[List[Dict]] = None,
        title: str = "Code",
        description: str = "",
        auto_connect: bool = True
    ) -> str:
        """
        添加 code 节点 + Block 包装器

        Args:
            code: Python 代码
            outputs: 输出变量列表
            args: 输入参数列表 (可选)
            title: 节点标题 (默认: "Code")
            description: 节点描述 (默认: "")
            auto_connect: 是否自动连接到前一个节点 (默认: True)

        Returns:
            str: Block 节点的 ID
        """
        # 注册输出变量
        for output in outputs:
            if "variable_assign" in output:
                self.variable_tracker.register(output["variable_assign"])

        # 生成位置
        functional_pos, block_pos = self.position_calc.get_node_pair_positions()

        # 生成 Block ID
        block_id = generate_uuid()

        # 创建功能节点
        functional_node = create_code_node(
            code=code,
            outputs=outputs,
            args=args,
            title=title,
            description=description,
            block_id=block_id,
            position_x=functional_pos["x"],
            position_y=functional_pos["y"]
        )

        # 创建 Block 包装器
        block_node = create_block_for_functional_node(
            functional_node_id=functional_node["id"],
            label=title,
            block_position=block_pos,
            block_id=block_id
        )

        # 添加到节点列表
        self.nodes.append(functional_node)
        self.nodes.append(block_node)

        # 存储 sourceHandle - 使用功能节点的 data.sourceHandle
        self.node_handles[block_id] = functional_node["data"]["sourceHandle"]

        # 存储双向映射
        self.block_to_func[block_id] = functional_node["id"]
        self.func_to_block[functional_node["id"]] = block_id

        # 自动连接
        if auto_connect and self.last_block_id:
            self.connect_nodes(self.last_block_id, block_id)

        self.last_block_id = block_id
        return block_id

    def add_llm_variable_assignment(
        self,
        prompt_template: str,
        variable_assign: str,
        llm_config: Optional[Dict] = None,
        title: str = "LLM Assignment",
        description: str = "",
        auto_connect: bool = True
    ) -> str:
        """
        添加 llmVariableAssignment 节点 + Block 包装器

        Args:
            prompt_template: Prompt 模板
            variable_assign: 要赋值的变量名
            llm_config: LLM 配置 (可选)
            title: 节点标题 (默认: "LLM Assignment")
            description: 节点描述 (默认: "")
            auto_connect: 是否自动连接到前一个节点 (默认: True)

        Returns:
            str: Block 节点的 ID
        """
        # 注册变量
        self.variable_tracker.register(variable_assign)

        # 生成位置
        functional_pos, block_pos = self.position_calc.get_node_pair_positions()

        # 生成 Block ID
        block_id = generate_uuid()

        # 创建功能节点
        functional_node = create_llm_variable_assignment_node(
            prompt_template=prompt_template,
            variable_assign=variable_assign,
            llm_config=llm_config,
            title=title,
            description=description,
            block_id=block_id,
            position_x=functional_pos["x"],
            position_y=functional_pos["y"]
        )

        # 创建 Block 包装器
        block_node = create_block_for_functional_node(
            functional_node_id=functional_node["id"],
            label=title,
            block_position=block_pos,
            block_id=block_id
        )

        # 添加到节点列表
        self.nodes.append(functional_node)
        self.nodes.append(block_node)

        # 存储 sourceHandle - 使用功能节点的 data.sourceHandle
        self.node_handles[block_id] = functional_node["data"]["sourceHandle"]

        # 存储双向映射
        self.block_to_func[block_id] = functional_node["id"]
        self.func_to_block[functional_node["id"]] = block_id

        # 自动连接
        if auto_connect and self.last_block_id:
            self.connect_nodes(self.last_block_id, block_id)

        self.last_block_id = block_id
        return block_id

    def add_llm_reply(
        self,
        prompt_template: str,
        llm_config: Optional[Dict] = None,
        title: str = "LLM Reply",
        description: str = "",
        auto_connect: bool = True
    ) -> str:
        """
        添加 llMReply 节点 + Block 包装器

        Args:
            prompt_template: Prompt 模板
            llm_config: LLM 配置 (可选)
            title: 节点标题 (默认: "LLM Reply")
            description: 节点描述 (默认: "")
            auto_connect: 是否自动连接到前一个节点 (默认: True)

        Returns:
            str: Block 节点的 ID
        """
        # 生成位置
        functional_pos, block_pos = self.position_calc.get_node_pair_positions()

        # 生成 Block ID
        block_id = generate_uuid()

        # 创建功能节点
        functional_node = create_llm_reply_node(
            prompt_template=prompt_template,
            llm_config=llm_config,
            title=title,
            description=description,
            block_id=block_id,
            position_x=functional_pos["x"],
            position_y=functional_pos["y"]
        )

        # 创建 Block 包装器
        block_node = create_block_for_functional_node(
            functional_node_id=functional_node["id"],
            label=title,
            block_position=block_pos,
            block_id=block_id
        )

        # 添加到节点列表
        self.nodes.append(functional_node)
        self.nodes.append(block_node)

        # 存储 sourceHandle - 使用功能节点的 data.sourceHandle
        self.node_handles[block_id] = functional_node["data"]["sourceHandle"]

        # 存储双向映射
        self.block_to_func[block_id] = functional_node["id"]
        self.func_to_block[functional_node["id"]] = block_id

        # 自动连接
        if auto_connect and self.last_block_id:
            self.connect_nodes(self.last_block_id, block_id)

        self.last_block_id = block_id
        return block_id

    # ============ 边连接方法 ============

    def connect_nodes(
        self,
        source_block_id: str,
        target_block_id: str,
        source_handle: Optional[str] = None,
        target_handle: Optional[str] = None
    ) -> Dict:
        """
        连接两个节点 (通过添加边)

        正确的边结构:
        - source: Block ID
        - target: Block ID
        - sourceHandle: 源功能节点的 data.sourceHandle
        - targetHandle: 目标功能节点的 ID

        Args:
            source_block_id: 源节点 ID (Block ID 或 start ID)
            target_block_id: 目标节点 ID (Block ID)
            source_handle: 源句柄 ID (可选,如果不指定则自动查找)
            target_handle: 目标句柄 ID (可选,默认为目标 Block 的功能节点 ID)

        Returns:
            dict: 创建的边
        """
        # 如果未指定 source_handle,尝试从存储中获取
        if source_handle is None and source_block_id in self.node_handles:
            source_handle = self.node_handles[source_block_id]

        # 如果未指定 target_handle,使用目标 Block 对应的功能节点 ID
        if target_handle is None:
            target_handle = self.block_to_func.get(target_block_id, target_block_id)

        edge = self.edge_manager.add_edge(
            source_block_id,
            target_block_id,
            source_handle,
            target_handle
        )
        return edge

    def connect_condition_branch(
        self,
        condition_block_id: str,
        condition_id: str,
        target_block_id: str
    ) -> Dict:
        """
        连接条件分支到目标节点

        Args:
            condition_block_id: Condition 节点的 block ID
            condition_id: 分支的 condition_id (从 add_condition 返回的列表中获取)
            target_block_id: 目标节点 ID (Block ID)

        Returns:
            dict: 创建的边
        """
        # 使用 condition_id 作为 sourceHandle
        # target 保持为 Block ID, targetHandle 自动解析为功能节点 ID
        return self.connect_nodes(
            condition_block_id,
            target_block_id,
            source_handle=condition_id
        )

    # ============ 导出方法 ============

    def to_json(self) -> Dict:
        """
        导出完整的 chatflow JSON

        Returns:
            dict: 完整的 chatflow JSON 结构
        """
        return {
            "created_by": self.created_by,
            "modified_by": self.modified_by,
            "flow_uuid": self.flow_uuid,
            "start_node_uuid": generate_start_node_id(),
            "intention_uuid": self.intention_uuid,
            "flow_name": self.flow_name,
            "description": self.description,
            "nodes": self.nodes,
            "edges": self.edge_manager.get_all_edges(),
            "buttons": [],
            "config": {},
            "intention_info": {},
            "entities": [],
            "lang": self.lang,
            "variables": self.variable_tracker.get_all_variables(),
            "categories": [],
            "position": [0, 0],
            "zoom": 1,
            "viewport": {
                "x": 0,
                "y": 0,
                "zoom": 1
            }
        }

    def to_json_string(self, indent: int = 2) -> str:
        """
        导出完整的 chatflow JSON 字符串

        Args:
            indent: JSON 缩进空格数 (默认: 2)

        Returns:
            str: JSON 字符串
        """
        return json.dumps(self.to_json(), indent=indent, ensure_ascii=False)

    def save(self, filepath: str, indent: int = 2) -> str:
        """
        保存 workflow 到文件

        Args:
            filepath: 文件路径 (绝对路径或相对路径)
            indent: JSON 缩进空格数 (默认: 2)

        Returns:
            str: 保存的文件路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json_string(indent=indent))
        return filepath

    # ============ 辅助方法 ============

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "flow_name": self.flow_name,
            "node_count": len(self.nodes),
            "edge_count": self.edge_manager.count(),
            "variable_count": self.variable_tracker.count(),
            "has_start_node": self.start_node is not None
        }

    def __repr__(self):
        stats = self.get_stats()
        return (f"Workflow(flow_name='{stats['flow_name']}', "
                f"nodes={stats['node_count']}, "
                f"edges={stats['edge_count']}, "
                f"variables={stats['variable_count']})")
