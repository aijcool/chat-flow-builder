"""
变量提取模块 - 从自然语言中提取变量名和描述
"""
import re
from typing import List, Dict, Optional


class VariableExtractor:
    """
    变量提取器 - 从文本中识别和提取变量信息

    支持多种表达方式:
    - "获取姓名" -> 变量名: name
    - "捕获用户邮箱" -> 变量名: email
    - "询问年龄并保存为age变量" -> 变量名: age
    """

    def __init__(self):
        """初始化变量提取器"""
        # 常见字段名映射 (中文 -> 英文变量名)
        self.field_mappings = {
            # 个人信息
            "姓名": "name",
            "名字": "name",
            "用户名": "username",
            "年龄": "age",
            "性别": "gender",
            "邮箱": "email",
            "电子邮箱": "email",
            "邮件": "email",
            "手机": "phone",
            "电话": "phone",
            "手机号": "phone",
            "电话号码": "phone",
            "地址": "address",
            "城市": "city",
            "国家": "country",

            # 业务信息
            "订单号": "order_id",
            "订单": "order",
            "产品": "product",
            "商品": "product",
            "数量": "quantity",
            "价格": "price",
            "金额": "amount",
            "日期": "date",
            "时间": "time",

            # 通用
            "输入": "user_input",
            "回复": "user_reply",
            "响应": "response",
            "结果": "result",
            "状态": "status",
            "信息": "info",
            "数据": "data"
        }

        # 变量命名模式
        self.variable_pattern = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')

    def extract_variable_from_text(self, text: str, context: Optional[str] = None) -> Optional[Dict]:
        """
        从文本中提取变量信息

        Args:
            text: 输入文本 (如 "获取用户姓名")
            context: 上下文信息 (可选)

        Returns:
            dict: 变量信息,格式:
                {
                    "variable_name": "name",
                    "description": "用户姓名",
                    "source_text": "获取用户姓名"
                }
                如果无法提取返回 None
        """
        # 1. 检查是否明确指定了变量名
        explicit_var = self._extract_explicit_variable(text)
        if explicit_var:
            return {
                "variable_name": explicit_var,
                "description": text,
                "source_text": text
            }

        # 2. 从常见字段映射中查找
        for field_name, var_name in self.field_mappings.items():
            if field_name in text:
                return {
                    "variable_name": var_name,
                    "description": field_name,
                    "source_text": text
                }

        # 3. 尝试从英文文本中提取
        english_var = self._extract_from_english(text)
        if english_var:
            return {
                "variable_name": english_var,
                "description": text,
                "source_text": text
            }

        # 4. 使用默认变量名
        return {
            "variable_name": "user_input",
            "description": "用户输入",
            "source_text": text
        }

    def _extract_explicit_variable(self, text: str) -> Optional[str]:
        """
        提取明确指定的变量名

        支持格式:
        - "保存为 age 变量"
        - "存入 email"
        - "赋值给 username"
        - "save as age"
        """
        patterns = [
            r'保存[为到]\s*(\w+)',
            r'存入\s*(\w+)',
            r'赋值给\s*(\w+)',
            r'变量\s*(\w+)',
            r'save\s+(?:as|to)\s+(\w+)',
            r'store\s+(?:in|as)\s+(\w+)',
            r'assign\s+to\s+(\w+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                var_name = match.group(1)
                if self.variable_pattern.fullmatch(var_name):
                    return var_name

        return None

    def _extract_from_english(self, text: str) -> Optional[str]:
        """
        从英文文本中提取变量名

        如 "get user name" -> "user_name"
        """
        # 常见动词列表
        verbs = ["get", "capture", "ask", "input", "receive", "collect", "fetch"]

        text_lower = text.lower()
        for verb in verbs:
            if text_lower.startswith(verb):
                # 移除动词,剩余部分作为变量名
                rest = text_lower[len(verb):].strip()
                # 转换为蛇形命名
                var_name = rest.replace(" ", "_").replace("-", "_")
                # 去除特殊字符
                var_name = re.sub(r'[^\w]', '', var_name)
                if var_name and self.variable_pattern.fullmatch(var_name):
                    return var_name

        return None

    def extract_multiple_variables(self, description: str) -> List[Dict]:
        """
        从描述中提取多个变量

        Args:
            description: 完整描述

        Returns:
            list: 变量信息列表
        """
        # 分句
        separators = [",", "，", ";", "。", ".", "、", "then", "然后", "接着"]
        pattern = "|".join(re.escape(sep) for sep in separators)
        sentences = re.split(pattern, description)

        variables = []
        seen_vars = set()

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 只对"获取/捕获"类句子提取变量
            if any(keyword in sentence.lower() for keyword in ["获取", "捕获", "询问", "问", "输入", "get", "capture", "ask", "input"]):
                var_info = self.extract_variable_from_text(sentence)
                if var_info and var_info["variable_name"] not in seen_vars:
                    variables.append(var_info)
                    seen_vars.add(var_info["variable_name"])

        return variables

    def infer_variable_type(self, description: str) -> str:
        """
        推断变量类型

        Args:
            description: 变量描述

        Returns:
            str: 变量类型 ("string", "number", "boolean")
        """
        desc_lower = description.lower()

        # 数字类型
        if any(keyword in desc_lower for keyword in ["年龄", "数量", "价格", "金额", "age", "quantity", "price", "amount", "count"]):
            return "number"

        # 布尔类型
        if any(keyword in desc_lower for keyword in ["是否", "whether", "是不是", "有没有", "flag"]):
            return "boolean"

        # 默认字符串
        return "string"

    def generate_variable_name(self, description: str, index: int = 0) -> str:
        """
        根据描述生成变量名

        Args:
            description: 描述文本
            index: 索引 (用于避免重复)

        Returns:
            str: 生成的变量名
        """
        var_info = self.extract_variable_from_text(description)
        base_name = var_info["variable_name"] if var_info else "var"

        if index > 0:
            return f"{base_name}_{index}"
        return base_name

    def __repr__(self):
        return f"VariableExtractor(mappings={len(self.field_mappings)})"
