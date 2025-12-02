"""
位置计算器模块 - 自动计算节点在画布上的位置
"""
from typing import Tuple, Dict


class PositionCalculator:
    """
    位置计算器类 - 根据规则自动计算节点位置

    布局规则:
    - 功能节点: 固定 x=125, y从325开始,每次递增200
    - Block 节点: x从475开始,每次递增350; y = functional_y - 50
    - Start 节点: 固定在 x=125, y=325
    """

    # 常量定义
    FUNCTIONAL_X = 125  # 功能节点固定 X 坐标
    FUNCTIONAL_START_Y = 325  # 功能节点起始 Y 坐标
    FUNCTIONAL_Y_INCREMENT = 200  # 功能节点 Y 坐标递增量

    BLOCK_START_X = 475  # Block 节点起始 X 坐标
    BLOCK_X_INCREMENT = 350  # Block 节点 X 坐标递增量
    BLOCK_Y_OFFSET = -50  # Block 相对于功能节点的 Y 偏移

    START_X = 125  # Start 节点 X 坐标
    START_Y = 325  # Start 节点 Y 坐标

    def __init__(self):
        """初始化位置计算器"""
        self.functional_node_count = 0  # 功能节点计数
        self.block_node_count = 0  # Block 节点计数

    def get_start_position(self) -> Dict[str, int]:
        """
        获取 start 节点的位置

        Returns:
            dict: 位置字典 {x, y}
        """
        return {"x": self.START_X, "y": self.START_Y}

    def get_functional_position(self) -> Dict[str, int]:
        """
        获取下一个功能节点的位置

        Returns:
            dict: 位置字典 {x, y}
        """
        y = self.FUNCTIONAL_START_Y + (self.functional_node_count * self.FUNCTIONAL_Y_INCREMENT)
        self.functional_node_count += 1
        return {"x": self.FUNCTIONAL_X, "y": y}

    def get_block_position(self, functional_y: int) -> Dict[str, int]:
        """
        获取 Block 节点的位置 (基于对应的功能节点 Y 坐标)

        Args:
            functional_y: 对应功能节点的 Y 坐标

        Returns:
            dict: 位置字典 {x, y}
        """
        x = self.BLOCK_START_X + (self.block_node_count * self.BLOCK_X_INCREMENT)
        y = functional_y + self.BLOCK_Y_OFFSET
        self.block_node_count += 1
        return {"x": x, "y": y}

    def get_node_pair_positions(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        获取一对节点 (功能节点 + Block 节点) 的位置

        Returns:
            tuple: (functional_position, block_position)
        """
        functional_pos = self.get_functional_position()
        block_pos = self.get_block_position(functional_pos["y"])
        return functional_pos, block_pos

    def reset(self):
        """重置计数器"""
        self.functional_node_count = 0
        self.block_node_count = 0

    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息

        Returns:
            dict: 统计信息 {functional_count, block_count}
        """
        return {
            "functional_count": self.functional_node_count,
            "block_count": self.block_node_count
        }
