"""
变量跟踪模块 - 管理 workflow 中的变量
"""
from typing import List, Dict, Set, Optional


class VariableTracker:
    """
    变量跟踪器 - 自动注册和管理 workflow 中使用的变量

    变量系统:
    - 所有变量必须在根级 variables 数组中声明
    - 引用语法: {{variable_name}}
    - 赋值方式: captureUserReply, code, llmVariableAssignment
    """

    def __init__(self, lang: str = "en"):
        """
        初始化变量跟踪器

        Args:
            lang: 语言代码 (默认: "en")
        """
        self.lang = lang
        self._variables: Dict[str, Dict[str, str]] = {}  # variable_name -> {description, lang}

    def register(self, variable_name: str, description: Optional[str] = None):
        """
        注册一个变量

        Args:
            variable_name: 变量名
            description: 变量描述 (可选)
        """
        if variable_name not in self._variables:
            self._variables[variable_name] = {
                "description": description or variable_name,
                "lang": self.lang
            }

    def is_registered(self, variable_name: str) -> bool:
        """
        检查变量是否已注册

        Args:
            variable_name: 变量名

        Returns:
            bool: 如果已注册返回 True,否则 False
        """
        return variable_name in self._variables

    def get_all_variables(self) -> List[Dict[str, str]]:
        """
        获取所有变量的声明列表 (用于生成 JSON)

        Returns:
            list: 变量声明列表,格式:
                [
                    {"variable_name": "name", "description": "user name", "lang": "en"},
                    ...
                ]
        """
        return [
            {
                "variable_name": name,
                "description": info["description"],
                "lang": info["lang"]
            }
            for name, info in self._variables.items()
        ]

    def get_variable_names(self) -> Set[str]:
        """
        获取所有变量名的集合

        Returns:
            set: 变量名集合
        """
        return set(self._variables.keys())

    def count(self) -> int:
        """
        获取已注册的变量数量

        Returns:
            int: 变量数量
        """
        return len(self._variables)

    def clear(self):
        """清除所有变量"""
        self._variables.clear()

    def update_description(self, variable_name: str, description: str):
        """
        更新变量描述

        Args:
            variable_name: 变量名
            description: 新的描述

        Raises:
            KeyError: 如果变量不存在
        """
        if variable_name not in self._variables:
            raise KeyError(f"Variable '{variable_name}' is not registered")

        self._variables[variable_name]["description"] = description

    def __contains__(self, variable_name: str) -> bool:
        """支持 'in' 操作符"""
        return variable_name in self._variables

    def __len__(self) -> int:
        """支持 len() 函数"""
        return len(self._variables)

    def __repr__(self):
        return f"VariableTracker(variables={list(self._variables.keys())}, count={len(self._variables)})"
