"""
意图检测模块 - 基于关键词检测用户描述中的节点类型
"""
import re
from typing import List, Dict, Optional


class IntentDetector:
    """
    意图检测器 - 识别自然语言中的节点类型和操作意图

    支持中英文关键词匹配
    """

    def __init__(self):
        """初始化意图检测器"""
        # 节点类型关键词映射
        self.node_keywords = {
            "textReply": {
                "zh": ["发送", "回复", "说", "告诉", "提示", "显示", "输出", "返回文本"],
                "en": ["send", "reply", "say", "tell", "show", "display", "output", "return text"]
            },
            "captureUserReply": {
                "zh": ["获取", "捕获", "询问", "问", "输入", "接收", "收集"],
                "en": ["get", "capture", "ask", "input", "receive", "collect", "prompt for"]
            },
            "condition": {
                "zh": ["如果", "判断", "检查", "条件", "分支", "是否", "当", "根据"],
                "en": ["if", "check", "condition", "branch", "when", "based on", "depending on"]
            },
            "code": {
                "zh": ["执行代码", "运行代码", "计算", "处理数据", "代码块"],
                "en": ["execute code", "run code", "calculate", "process", "code block"]
            },
            "llmVariableAssignment": {
                "zh": ["LLM提取", "LLM处理", "AI提取", "AI处理", "智能提取", "分析提取"],
                "en": ["LLM extract", "AI extract", "LLM process", "AI process", "smart extract", "analyze"]
            },
            "llMReply": {
                "zh": ["LLM回复", "AI回复", "智能回复", "AI生成", "LLM生成"],
                "en": ["LLM reply", "AI reply", "smart reply", "AI generate", "LLM generate"]
            }
        }

        # 变量引用模式
        self.variable_pattern = re.compile(r'\{\{(\w+)\}\}|{{(\w+)}}')

    def detect_node_type(self, text: str, lang: str = "auto") -> Optional[str]:
        """
        检测文本中的节点类型

        Args:
            text: 输入文本
            lang: 语言 ("zh", "en", "auto" 自动检测)

        Returns:
            str: 节点类型 (textReply, captureUserReply, condition, code, llmVariableAssignment, llMReply)
                 如果无法确定返回 None
        """
        text_lower = text.lower()

        # 自动检测语言
        if lang == "auto":
            lang = "zh" if self._contains_chinese(text) else "en"

        # 按优先级检查关键词
        scores = {}
        for node_type, keywords in self.node_keywords.items():
            score = 0
            for keyword in keywords.get(lang, []):
                if keyword.lower() in text_lower:
                    score += 1
            if score > 0:
                scores[node_type] = score

        # 返回得分最高的节点类型
        if scores:
            return max(scores, key=scores.get)

        # 如果没有明确关键词,根据语义推断
        # "问" + "获取" 通常是 ask + capture 的组合
        if any(k in text_lower for k in ["询问", "ask", "问"]):
            if any(k in text_lower for k in ["获取", "捕获", "输入", "get", "capture", "input"]):
                return "captureUserReply"

        return None

    def detect_node_sequence(self, description: str, lang: str = "auto") -> List[Dict]:
        """
        从描述中检测节点序列

        Args:
            description: 自然语言描述
            lang: 语言 ("zh", "en", "auto")

        Returns:
            list: 节点序列,格式:
                [
                    {"type": "textReply", "text": "询问姓名"},
                    {"type": "captureUserReply", "text": "获取姓名"},
                    ...
                ]
        """
        # 自动检测语言
        if lang == "auto":
            lang = "zh" if self._contains_chinese(description) else "en"

        # 分句 (支持中英文分隔符)
        separators = [",", "，", ";", "。", ".", "、", "then", "然后", "接着", "之后"]
        pattern = "|".join(re.escape(sep) for sep in separators)
        sentences = re.split(pattern, description)

        nodes = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 检测节点类型
            node_type = self.detect_node_type(sentence, lang)
            if node_type:
                nodes.append({
                    "type": node_type,
                    "text": sentence,
                    "raw": sentence
                })

        return nodes

    def extract_variables_from_text(self, text: str) -> List[str]:
        """
        从文本中提取变量引用 ({{variable_name}} 格式)

        Args:
            text: 输入文本

        Returns:
            list: 变量名列表
        """
        matches = self.variable_pattern.findall(text)
        # findall 返回 tuple (group1, group2),需要合并
        variables = []
        for match in matches:
            var = match[0] or match[1]
            if var and var not in variables:
                variables.append(var)
        return variables

    def is_question(self, text: str) -> bool:
        """
        判断文本是否是问题

        Args:
            text: 输入文本

        Returns:
            bool: 是否是问题
        """
        # 检查问号
        if "?" in text or "?" in text:
            return True

        # 检查疑问词
        question_words = [
            "什么", "哪", "谁", "何", "怎么", "为什么", "多少", "几",  # 中文
            "what", "which", "who", "where", "when", "why", "how", "can", "do", "does"  # 英文
        ]
        text_lower = text.lower()
        return any(word in text_lower for word in question_words)

    def _contains_chinese(self, text: str) -> bool:
        """
        检查文本是否包含中文

        Args:
            text: 输入文本

        Returns:
            bool: 是否包含中文
        """
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def detect_condition_type(self, text: str) -> Optional[Dict]:
        """
        检测条件类型和比较操作

        Args:
            text: 条件描述文本

        Returns:
            dict: 条件信息,格式:
                {
                    "variable": "age",
                    "operator": ">=",
                    "value": "18"
                }
                如果无法解析返回 None
        """
        # 常见条件模式
        patterns = [
            # 大于等于
            (r'(\w+)\s*>=\s*(\d+)', ">="),
            (r'(\w+)\s*≥\s*(\d+)', ">="),
            (r'(\w+)\s*大于等于\s*(\d+)', ">="),
            (r'(\w+)\s*不小于\s*(\d+)', ">="),

            # 小于等于
            (r'(\w+)\s*<=\s*(\d+)', "<="),
            (r'(\w+)\s*≤\s*(\d+)', "<="),
            (r'(\w+)\s*小于等于\s*(\d+)', "<="),
            (r'(\w+)\s*不大于\s*(\d+)', "<="),

            # 大于
            (r'(\w+)\s*>\s*(\d+)', ">"),
            (r'(\w+)\s*大于\s*(\d+)', ">"),

            # 小于
            (r'(\w+)\s*<\s*(\d+)', "<"),
            (r'(\w+)\s*小于\s*(\d+)', "<"),

            # 等于
            (r'(\w+)\s*==\s*["\']?(\w+)["\']?', "="),
            (r'(\w+)\s*=\s*["\']?(\w+)["\']?', "="),
            (r'(\w+)\s*等于\s*["\']?(\w+)["\']?', "="),
            (r'(\w+)\s*是\s*["\']?(\w+)["\']?', "="),
        ]

        for pattern, operator in patterns:
            match = re.search(pattern, text)
            if match:
                return {
                    "variable": match.group(1),
                    "operator": operator,
                    "value": match.group(2)
                }

        return None

    def __repr__(self):
        return f"IntentDetector(node_types={len(self.node_keywords)})"
