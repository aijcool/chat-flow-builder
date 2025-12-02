"""
自然语言解析器 - 将自然语言描述转换为结构化的 workflow 步骤
"""
from typing import List, Dict, Optional
from .intent_detector import IntentDetector
from .variable_extractor import VariableExtractor


class NLParser:
    """
    自然语言解析器

    功能:
    - 解析自然语言描述为节点序列
    - 识别节点类型和参数
    - 提取变量信息
    - 生成可执行的步骤列表
    """

    def __init__(self, lang: str = "auto"):
        """
        初始化解析器

        Args:
            lang: 语言 ("zh", "en", "auto" 自动检测)
        """
        self.lang = lang
        self.intent_detector = IntentDetector()
        self.variable_extractor = VariableExtractor()

    def parse(self, description: str) -> Dict:
        """
        解析自然语言描述

        Args:
            description: 自然语言描述

        Returns:
            dict: 解析结果,格式:
                {
                    "steps": [
                        {
                            "type": "textReply",
                            "config": {"text": "..."},
                            "description": "..."
                        },
                        ...
                    ],
                    "variables": [
                        {
                            "variable_name": "name",
                            "description": "用户姓名"
                        },
                        ...
                    ],
                    "meta": {
                        "total_steps": 5,
                        "node_types": ["textReply", "captureUserReply", ...]
                    }
                }
        """
        # 检测节点序列
        node_sequence = self.intent_detector.detect_node_sequence(description, self.lang)

        # 转换为结构化步骤
        steps = []
        variables = []
        seen_vars = set()

        for i, node_info in enumerate(node_sequence):
            step = self._convert_to_step(node_info, i, seen_vars)
            if step:
                steps.append(step)

                # 收集变量信息
                if "variable" in step["config"]:
                    var_name = step["config"]["variable"]
                    if var_name not in seen_vars:
                        variables.append({
                            "variable_name": var_name,
                            "description": step.get("description", var_name)
                        })
                        seen_vars.add(var_name)

        # 元信息
        meta = {
            "total_steps": len(steps),
            "node_types": list(set(step["type"] for step in steps)),
            "variable_count": len(variables)
        }

        return {
            "steps": steps,
            "variables": variables,
            "meta": meta
        }

    def _convert_to_step(self, node_info: Dict, index: int, seen_vars: set) -> Optional[Dict]:
        """
        将节点信息转换为结构化步骤

        Args:
            node_info: 节点信息 (from intent_detector)
            index: 节点索引
            seen_vars: 已见过的变量集合

        Returns:
            dict: 步骤配置
        """
        node_type = node_info["type"]
        text = node_info["text"]

        if node_type == "textReply":
            return self._create_text_reply_step(text, index)

        elif node_type == "captureUserReply":
            return self._create_capture_step(text, index, seen_vars)

        elif node_type == "condition":
            return self._create_condition_step(text, index)

        elif node_type == "code":
            return self._create_code_step(text, index)

        elif node_type == "llmVariableAssignment":
            return self._create_llm_assignment_step(text, index, seen_vars)

        elif node_type == "llMReply":
            return self._create_llm_reply_step(text, index)

        return None

    def _create_text_reply_step(self, text: str, index: int) -> Dict:
        """创建 textReply 步骤"""
        # 清理文本 (移除 "发送", "回复" 等动词)
        clean_text = self._clean_action_words(text, ["发送", "回复", "说", "告诉", "send", "reply", "say"])

        return {
            "type": "textReply",
            "config": {
                "text": clean_text or text,
                "title": f"Response_{index + 1}"
            },
            "description": text
        }

    def _create_capture_step(self, text: str, index: int, seen_vars: set) -> Dict:
        """创建 captureUserReply 步骤"""
        # 提取变量信息
        var_info = self.variable_extractor.extract_variable_from_text(text)

        # 避免变量名重复
        var_name = var_info["variable_name"]
        if var_name in seen_vars:
            counter = 1
            while f"{var_name}_{counter}" in seen_vars:
                counter += 1
            var_name = f"{var_name}_{counter}"

        return {
            "type": "captureUserReply",
            "config": {
                "variable": var_name,
                "title": f"Capture_{index + 1}"
            },
            "description": var_info["description"]
        }

    def _create_condition_step(self, text: str, index: int) -> Dict:
        """创建 condition 步骤"""
        # 尝试解析条件
        condition_info = self.intent_detector.detect_condition_type(text)

        if condition_info:
            # 创建简单的两分支条件
            return {
                "type": "condition",
                "config": {
                    "if_else_conditions": [
                        {
                            "condition_name": "条件满足",
                            "logical_operator": "and",
                            "conditions": [
                                {
                                    "condition_type": "variable",
                                    "comparison_operator": condition_info["operator"],
                                    "condition_value": condition_info["value"],
                                    "condition_variable": condition_info["variable"]
                                }
                            ],
                            "condition_action": []
                        },
                        {
                            "condition_name": "Other",
                            "logical_operator": "other",
                            "conditions": [],
                            "condition_action": []
                        }
                    ],
                    "title": f"Condition_{index + 1}"
                },
                "description": text
            }
        else:
            # 无法解析具体条件,返回模板
            return {
                "type": "condition",
                "config": {
                    "if_else_conditions": [
                        {
                            "condition_name": "分支1",
                            "logical_operator": "and",
                            "conditions": [
                                {
                                    "condition_type": "variable",
                                    "comparison_operator": "=",
                                    "condition_value": "value",
                                    "condition_variable": "variable"
                                }
                            ],
                            "condition_action": []
                        },
                        {
                            "condition_name": "Other",
                            "logical_operator": "other",
                            "conditions": [],
                            "condition_action": []
                        }
                    ],
                    "title": f"Condition_{index + 1}"
                },
                "description": text,
                "note": "需要手动配置条件"
            }

    def _create_code_step(self, text: str, index: int) -> Dict:
        """创建 code 步骤"""
        return {
            "type": "code",
            "config": {
                "code": "def main() -> dict:\n    # TODO: 实现代码逻辑\n    return {\"result\": \"success\"}",
                "outputs": [
                    {
                        "name": "result",
                        "type": "string",
                        "variable_assign": "result"
                    }
                ],
                "args": [],
                "title": f"Code_{index + 1}"
            },
            "description": text,
            "note": "需要手动实现代码"
        }

    def _create_llm_assignment_step(self, text: str, index: int, seen_vars: set) -> Dict:
        """创建 llmVariableAssignment 步骤"""
        # 提取目标变量
        var_info = self.variable_extractor.extract_variable_from_text(text)
        var_name = var_info["variable_name"]

        if var_name in seen_vars:
            counter = 1
            while f"{var_name}_{counter}" in seen_vars:
                counter += 1
            var_name = f"{var_name}_{counter}"

        # 清理文本作为 prompt 模板
        clean_text = self._clean_action_words(text, ["LLM提取", "LLM处理", "AI提取", "AI处理", "提取", "处理"])

        return {
            "type": "llmVariableAssignment",
            "config": {
                "prompt_template": f"用户输入: {{{{user_input}}}}\n\n请{clean_text}",
                "variable": var_name,
                "title": f"LLM_Assignment_{index + 1}"
            },
            "description": text
        }

    def _create_llm_reply_step(self, text: str, index: int) -> Dict:
        """创建 llMReply 步骤"""
        # 清理文本作为 prompt 模板
        clean_text = self._clean_action_words(text, ["LLM回复", "AI回复", "智能回复", "回复", "生成"])

        return {
            "type": "llMReply",
            "config": {
                "prompt_template": f"请根据上下文{clean_text}",
                "title": f"LLM_Reply_{index + 1}"
            },
            "description": text
        }

    def _clean_action_words(self, text: str, action_words: List[str]) -> str:
        """
        清理动词和动作词

        Args:
            text: 原始文本
            action_words: 要移除的动作词列表

        Returns:
            str: 清理后的文本
        """
        cleaned = text
        for word in action_words:
            cleaned = cleaned.replace(word, "")

        return cleaned.strip()

    def parse_quick(self, description: str) -> List[Dict]:
        """
        快速解析 - 只返回步骤列表 (简化版)

        Args:
            description: 自然语言描述

        Returns:
            list: 步骤列表
        """
        result = self.parse(description)
        return result["steps"]

    def __repr__(self):
        return f"NLParser(lang='{self.lang}')"
