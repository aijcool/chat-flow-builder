"""
边连接模块 - 创建节点之间的连接
"""
from typing import Dict, Optional


def create_edge(
    source_block_id: str,
    target_block_id: str,
    source_handle: Optional[str] = None,
    target_handle: Optional[str] = None,
    source_x: int = 0,
    source_y: int = 0,
    target_x: int = 0,
    target_y: int = 0
) -> Dict:
    """
    创建一条边

    Args:
        source_block_id: 源节点的 block ID
        target_block_id: 目标节点的 block ID
        source_handle: 源句柄 ID (可选,对于条件节点必须指定)
        target_handle: 目标句柄 ID (可选,通常等于 target_block_id)
        source_x: 源节点 X 坐标 (用于渲染)
        source_y: 源节点 Y 坐标 (用于渲染)
        target_x: 目标节点 X 坐标 (用于渲染)
        target_y: 目标节点 Y 坐标 (用于渲染)

    Returns:
        dict: 边配置

    边结构规范:
    - id: 自动生成,格式 vueflow__edge-{source}{source_handle}-{target}{target_handle}
    - type: "custom"
    - source: 源 block ID
    - target: 目标 block ID
    - sourceHandle: 源句柄 (条件分支必须匹配 condition_id)
    - targetHandle: 目标句柄 (通常等于 target ID)
    """
    # 如果未指定 handle,使用默认值
    if source_handle is None:
        source_handle = source_block_id

    if target_handle is None:
        target_handle = target_block_id

    # 生成边 ID (按照 vueflow 格式)
    edge_id = f"vueflow__edge-{source_block_id}{source_handle}-{target_block_id}{target_handle}"

    return {
        "id": edge_id,
        "type": "custom",
        "source": source_block_id,
        "target": target_block_id,
        "sourceHandle": source_handle,
        "targetHandle": target_handle,
        "data": {"hovering": False},
        "label": "",
        "sourceX": source_x,
        "sourceY": source_y,
        "targetX": target_x,
        "targetY": target_y,
        "zIndex": 0,
        "animated": False
    }


class EdgeManager:
    """边管理器 - 管理 workflow 中的所有边"""

    def __init__(self):
        """初始化边管理器"""
        self.edges: list[Dict] = []

    def add_edge(
        self,
        source_block_id: str,
        target_block_id: str,
        source_handle: Optional[str] = None,
        target_handle: Optional[str] = None
    ) -> Dict:
        """
        添加一条边

        Args:
            source_block_id: 源 block ID
            target_block_id: 目标 block ID
            source_handle: 源句柄 (可选)
            target_handle: 目标句柄 (可选)

        Returns:
            dict: 创建的边配置
        """
        edge = create_edge(
            source_block_id,
            target_block_id,
            source_handle,
            target_handle
        )
        self.edges.append(edge)
        return edge

    def get_all_edges(self) -> list[Dict]:
        """
        获取所有边

        Returns:
            list: 边列表
        """
        return self.edges

    def count(self) -> int:
        """
        获取边的数量

        Returns:
            int: 边数量
        """
        return len(self.edges)

    def clear(self):
        """清除所有边"""
        self.edges.clear()

    def find_edges_from_node(self, node_id: str) -> list[Dict]:
        """
        查找从指定节点出发的所有边

        Args:
            node_id: 节点 ID

        Returns:
            list: 边列表
        """
        return [edge for edge in self.edges if edge["source"] == node_id]

    def find_edges_to_node(self, node_id: str) -> list[Dict]:
        """
        查找到达指定节点的所有边

        Args:
            node_id: 节点 ID

        Returns:
            list: 边列表
        """
        return [edge for edge in self.edges if edge["target"] == node_id]

    def __len__(self) -> int:
        """支持 len() 函数"""
        return len(self.edges)

    def __repr__(self):
        return f"EdgeManager(edges_count={len(self.edges)})"
