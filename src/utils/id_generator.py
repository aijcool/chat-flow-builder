"""
ID 生成器模块 - 生成 UUID 用于节点、边等
"""
import uuid


def generate_uuid() -> str:
    """
    生成一个新的 UUID (UUID4)

    Returns:
        str: UUID 字符串 (格式: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    """
    return str(uuid.uuid4())


def generate_start_node_id() -> str:
    """
    生成 start 节点的固定 ID

    Returns:
        str: 固定的 start 节点 ID
    """
    return "start00000000000000000000"


class IDGenerator:
    """ID 生成器类 - 用于批量生成和跟踪 ID"""

    def __init__(self):
        """初始化 ID 生成器"""
        self.generated_ids = set()

    def generate(self) -> str:
        """
        生成一个新的唯一 UUID

        Returns:
            str: 唯一的 UUID 字符串
        """
        new_id = generate_uuid()
        # 确保 ID 唯一 (虽然 UUID4 碰撞概率极低)
        while new_id in self.generated_ids:
            new_id = generate_uuid()

        self.generated_ids.add(new_id)
        return new_id

    def is_generated(self, id_str: str) -> bool:
        """
        检查 ID 是否已经生成过

        Args:
            id_str: 要检查的 ID

        Returns:
            bool: 如果 ID 已生成返回 True,否则返回 False
        """
        return id_str in self.generated_ids

    def clear(self):
        """清除所有已生成的 ID 记录"""
        self.generated_ids.clear()

    def count(self) -> int:
        """
        获取已生成的 ID 数量

        Returns:
            int: ID 数量
        """
        return len(self.generated_ids)
