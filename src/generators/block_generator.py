"""
Block 包装器生成模块 - 为功能节点生成可视化的 Block 包装器
"""
from typing import Dict, List, Optional
from ..utils.id_generator import generate_uuid


def create_block_node(
    block_id: str,
    include_node_ids: List[str],
    label: str,
    position_x: int,
    position_y: int,
    target_position: str = "left",
    source_position: str = "right"
) -> Dict:
    """
    创建一个 Block 包装器节点

    Args:
        block_id: Block 节点的 ID (通常是 UUID)
        include_node_ids: 包含的功能节点 ID 列表
        label: Block 的标签 (显示名称)
        position_x: X 坐标
        position_y: Y 坐标
        target_position: 目标句柄位置 (默认: "left")
        source_position: 源句柄位置 (默认: "right")

    Returns:
        dict: Block 节点配置

    Block 节点规范:
    - type: "block"
    - data.include_node_ids: 包含的功能节点 ID 列表
    - data.label: 显示标签
    - position: 相对于功能节点偏移 (x + 350, y - 50)
    - hidden: 不设置 (默认为 visible)
    """
    return {
        "id": block_id,
        "type": "block",
        "initialized": False,
        "position": {
            "x": position_x,
            "y": position_y
        },
        "data": {
            "label": label,
            "include_node_ids": include_node_ids,
            "showToolBar": False,
            "targetPosition": target_position,
            "sourcePosition": source_position
        }
    }


def create_block_for_functional_node(
    functional_node_id: str,
    label: str,
    block_position: Dict[str, int],
    block_id: Optional[str] = None
) -> Dict:
    """
    为单个功能节点创建 Block 包装器 (常见用法)

    Args:
        functional_node_id: 功能节点的 ID
        label: Block 的标签
        block_position: Block 的位置 {"x": int, "y": int}
        block_id: Block ID (可选,默认自动生成 UUID)

    Returns:
        dict: Block 节点配置
    """
    if block_id is None:
        block_id = generate_uuid()

    return create_block_node(
        block_id=block_id,
        include_node_ids=[functional_node_id],
        label=label,
        position_x=block_position["x"],
        position_y=block_position["y"]
    )


class BlockGenerator:
    """Block 生成器类 - 批量管理 Block 节点生成"""

    def __init__(self):
        """初始化 Block 生成器"""
        self.blocks: List[Dict] = []

    def generate_block(
        self,
        functional_node_id: str,
        label: str,
        block_position: Dict[str, int]
    ) -> Dict:
        """
        生成一个 Block 并添加到列表

        Args:
            functional_node_id: 功能节点 ID
            label: Block 标签
            block_position: Block 位置

        Returns:
            dict: 生成的 Block 节点
        """
        block = create_block_for_functional_node(
            functional_node_id,
            label,
            block_position
        )
        self.blocks.append(block)
        return block

    def get_all_blocks(self) -> List[Dict]:
        """
        获取所有生成的 Block 节点

        Returns:
            list: Block 节点列表
        """
        return self.blocks

    def count(self) -> int:
        """
        获取 Block 数量

        Returns:
            int: Block 数量
        """
        return len(self.blocks)

    def clear(self):
        """清除所有 Block"""
        self.blocks.clear()

    def __len__(self) -> int:
        """支持 len() 函数"""
        return len(self.blocks)

    def __repr__(self):
        return f"BlockGenerator(blocks_count={len(self.blocks)})"
