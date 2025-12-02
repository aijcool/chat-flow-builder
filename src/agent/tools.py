"""
Agent 工具定义 - 为 Claude Agent 提供的工具函数
"""
import json
import os
import requests
from typing import Dict, List, Optional
from urllib.parse import quote_plus
from dotenv import load_dotenv
from ..parsers.nl_parser import NLParser
from ..core.workflow import Workflow

# 加载 .env 文件
load_dotenv()

# Supabase 配置
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = "workflows"

# 调试输出
print(f"[tools.py] SUPABASE_URL = {SUPABASE_URL[:50] if SUPABASE_URL else 'NOT SET'}...")


# ============ 工具函数实现 ============

def parse_workflow_description(description: str, lang: str = "auto") -> Dict:
    """
    工具 1: 解析自然语言描述为结构化步骤

    Args:
        description: 自然语言描述
        lang: 语言 ("zh", "en", "auto")

    Returns:
        dict: 解析结果,包含 steps, variables, meta
    """
    parser = NLParser(lang=lang)
    result = parser.parse(description)

    return {
        "success": True,
        "steps": result["steps"],
        "variables": result["variables"],
        "meta": result["meta"],
        "message": f"成功解析 {result['meta']['total_steps']} 个步骤"
    }


def generate_workflow(
    workflow_name: str,
    steps: List[Dict],
    description: str = "",
    lang: str = "en",
    user_id: str = "public"
) -> Dict:
    """
    工具 2: 根据步骤生成完整的 workflow JSON 并自动保存到 Supabase

    Args:
        workflow_name: 工作流名称 (同时用作文件名)
        steps: 步骤列表 (from parse_workflow_description)
        description: 工作流描述 (可选)
        lang: 语言代码 (默认: "en")
        user_id: 用户 ID (默认: "public")

    Returns:
        dict: 生成结果，包含文件名和 Supabase URL（不含完整 workflow）
    """
    try:
        # 创建 workflow
        workflow = Workflow(workflow_name, description, lang=lang)

        # 添加 start 节点
        workflow.add_start_node()

        # 添加所有步骤
        for step in steps:
            step_type = step.get("type", "")
            # 兼容两种格式：
            # 1. {"type": "...", "config": {...}} - 来自 parse_workflow_description
            # 2. {"type": "...", "text": "...", "title": "..."} - Claude 直接构造
            config = step.get("config", step)  # 如果没有 config 字段，使用 step 本身

            if step_type == "textReply":
                workflow.add_text_reply(
                    text=config.get("text", ""),
                    title=config.get("title", "Response")
                )

            elif step_type == "captureUserReply":
                # 兼容 variable / variableName / variable_name
                var_name = config.get("variable") or config.get("variableName") or config.get("variable_name", "user_input")
                workflow.add_capture_user_reply(
                    variable_name=var_name,
                    description=config.get("description") or step.get("description"),
                    title=config.get("title", "Capture")
                )

            elif step_type == "condition":
                # 兼容多种条件格式
                if_else = config.get("if_else_conditions")
                if not if_else:
                    # 尝试从简化格式构建条件
                    condition_str = config.get("condition") or config.get("expression", "")
                    condition_var = config.get("variable") or config.get("condition_variable", "")
                    condition_value = config.get("value") or config.get("condition_value", "")
                    condition_name = config.get("condition_name") or config.get("name", "条件判断")

                    if condition_str or (condition_var and condition_value):
                        # 构建完整的条件结构
                        if_else = [{
                            "condition_name": condition_name,
                            "logical_operator": "and",
                            "conditions": [{
                                "condition_type": "variable",
                                "comparison_operator": config.get("operator", "="),
                                "condition_value": condition_value or condition_str,
                                "condition_variable": condition_var or condition_str.split()[0] if condition_str else ""
                            }],
                            "condition_action": []
                        }]
                    else:
                        # 默认空条件
                        if_else = [{
                            "condition_name": condition_name,
                            "logical_operator": "and",
                            "conditions": [],
                            "condition_action": []
                        }]

                workflow.add_condition(
                    if_else_conditions=if_else,
                    title=config.get("title", "Condition")
                )

            elif step_type == "code":
                workflow.add_code(
                    code=config.get("code", ""),
                    outputs=config.get("outputs", []),
                    args=config.get("args", []),
                    title=config.get("title", "Code")
                )

            elif step_type == "llmVariableAssignment":
                prompt = config.get("prompt_template") or config.get("prompt", "")
                var_assign = config.get("variable") or config.get("variableName") or config.get("variable_assign", "result")
                workflow.add_llm_variable_assignment(
                    prompt_template=prompt,
                    variable_assign=var_assign,
                    title=config.get("title", "LLM Assignment")
                )

            elif step_type == "llMReply" or step_type == "llmReply":
                prompt = config.get("prompt_template") or config.get("prompt") or config.get("message", "")
                workflow.add_llm_reply(
                    prompt_template=prompt,
                    title=config.get("title", "LLM Reply")
                )

        # 获取统计信息
        stats = workflow.get_stats()
        workflow_json = workflow.to_json()

        # 自动保存到 Supabase Storage
        save_result = save_workflow_to_file(
            workflow=workflow_json,
            filename=workflow_name,
            user_id=user_id
        )

        if not save_result.get("success"):
            return save_result

        # 返回简化结果（不含完整 workflow JSON）
        return {
            "success": True,
            "filename": save_result.get("filename"),
            "storage_url": save_result.get("storage_url"),
            "stats": stats,
            "message": f"成功生成并保存 [{save_result.get('filename')}]，包含 {stats['node_count']} 个节点"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"生成失败: {str(e)}"
        }


def validate_workflow(workflow: Dict) -> Dict:
    """
    工具 3: 验证 workflow JSON 的结构

    Args:
        workflow: workflow JSON

    Returns:
        dict: 验证结果
    """
    errors = []
    warnings = []

    # 兼容两种格式：
    # 1. 标准格式：{"flow_name": "...", "nodes": [...], "edges": [...]}
    # 2. Claude 构造的格式：{"startNodes": [...], "nodes": {...}}
    nodes = workflow.get("nodes", [])

    # 如果 nodes 是字典格式（Claude 构造的），转换为列表
    if isinstance(nodes, dict):
        warnings.append("节点格式为字典，建议使用标准列表格式")
        # 简单验证：检查是否有节点
        if len(nodes) == 0:
            errors.append("没有定义任何节点")
        # 返回基本验证结果
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "message": "验证通过（非标准格式）" if len(errors) == 0 else f"验证失败: {len(errors)} 个错误"
        }

    # 标准格式验证
    required_fields = ["flow_name", "nodes", "edges", "variables"]
    for field in required_fields:
        if field not in workflow:
            errors.append(f"缺少必需字段: {field}")

    # 检查 start 节点
    if isinstance(nodes, list) and len(nodes) > 0:
        start_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "start"]
        if len(start_nodes) == 0:
            errors.append("缺少 start 节点")
        elif len(start_nodes) > 1:
            errors.append("存在多个 start 节点")

        # 检查每个功能节点是否有 Block 包装器
        functional_nodes = [n for n in nodes if isinstance(n, dict) and n.get("hidden") is True]
        block_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "block"]

        if len(functional_nodes) > 0 and len(block_nodes) != len(functional_nodes):
            warnings.append(f"功能节点数量 ({len(functional_nodes)}) 与 Block 数量 ({len(block_nodes)}) 不匹配")

    # 检查变量引用
    variables = workflow.get("variables", [])
    if isinstance(variables, list) and len(variables) > 0:
        try:
            declared_vars = set(v.get("variable_name", "") for v in variables if isinstance(v, dict))
            # TODO: 检查节点中引用的变量是否都已声明
        except Exception:
            pass  # 忽略格式错误

    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "message": "验证通过" if valid else f"验证失败: {len(errors)} 个错误"
    }


def save_workflow_to_file(
    workflow: Dict,
    filename: str,
    user_id: str = "public"
) -> Dict:
    """
    工具 4: 保存 workflow 到 Supabase Storage

    Args:
        workflow: workflow JSON
        filename: 文件名 (不含路径,如 "my_workflow.json")
        user_id: 用户 ID (默认: "public")

    Returns:
        dict: 保存结果，包含 storage_url
    """
    try:
        # 确保文件名以 .json 结尾
        if not filename.endswith('.json'):
            filename = f"{filename}.json"

        base_name = filename[:-5]  # 去掉 .json
        final_filename = filename
        storage_path = f"{user_id}/{final_filename}"

        # 准备上传内容
        content = json.dumps(workflow, indent=2, ensure_ascii=False)
        content_bytes = content.encode('utf-8')

        # 上传到 Supabase Storage
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }

        # 先尝试上传
        response = requests.post(upload_url, headers=headers, data=content_bytes)

        # 如果文件已存在 (409 Conflict 或 400)，添加序号重试
        counter = 1
        while response.status_code in [400, 409] and counter < 100:
            final_filename = f"{base_name}_{counter}.json"
            storage_path = f"{user_id}/{final_filename}"
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
            response = requests.post(upload_url, headers=headers, data=content_bytes)
            counter += 1

        if response.status_code not in [200, 201]:
            return {
                "success": False,
                "error": f"Upload failed: {response.status_code} - {response.text}",
                "message": f"上传失败: {response.text}"
            }

        # 构建公开访问 URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        # 计算节点数量
        node_count = len(workflow.get("nodes", []))

        return {
            "success": True,
            "filename": final_filename,
            "storage_path": storage_path,
            "storage_url": public_url,
            "file_size": len(content_bytes),
            "node_count": node_count,
            "message": f"成功保存 [{final_filename}]，包含 {node_count} 个节点"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"保存失败: {str(e)}"
        }


def list_workflow_files(user_id: str = "public") -> Dict:
    """
    工具 5: 列出 Supabase Storage 中的工作流文件

    Args:
        user_id: 用户 ID (默认: "public")

    Returns:
        dict: 文件列表
    """
    try:
        # 调用 Supabase Storage API 列出文件
        list_url = f"{SUPABASE_URL}/storage/v1/object/list/{SUPABASE_BUCKET}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            list_url,
            headers=headers,
            json={"prefix": f"{user_id}/", "limit": 100}
        )

        if response.status_code != 200:
            return {"success": True, "files": [], "message": "目录为空"}

        data = response.json()
        files = [
            {
                "name": item["name"],
                "url": f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{user_id}/{item['name']}",
                "created_at": item.get("created_at"),
                "size": item.get("metadata", {}).get("size", 0)
            }
            for item in data
            if item["name"].endswith('.json')
        ]

        return {
            "success": True,
            "files": files,
            "count": len(files),
            "message": f"找到 {len(files)} 个工作流文件"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"列出文件失败: {str(e)}"
        }


def load_workflow_from_file(
    filename: str,
    user_id: str = "public"
) -> Dict:
    """
    工具 6: 从 Supabase Storage 加载工作流

    Args:
        filename: 文件名
        user_id: 用户 ID (默认: "public")

    Returns:
        dict: 加载的工作流数据
    """
    try:
        if not filename.endswith('.json'):
            filename = f"{filename}.json"

        # 从 Supabase Storage 下载
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)

        if response.status_code != 200:
            return {
                "success": False,
                "error": "文件不存在",
                "message": f"文件 {filename} 不存在"
            }

        workflow = response.json()

        # 提取摘要信息
        node_count = len(workflow.get('nodes', []))
        edge_count = len(workflow.get('edges', []))
        variable_count = len(workflow.get('variables', []))

        # 提取节点类型列表
        node_types = {}
        for node in workflow.get('nodes', []):
            ntype = node.get('type', 'unknown')
            node_types[ntype] = node_types.get(ntype, 0) + 1

        return {
            "success": True,
            "workflow": workflow,
            "storage_url": download_url,
            "summary": {
                "node_count": node_count,
                "edge_count": edge_count,
                "variable_count": variable_count,
                "node_types": node_types
            },
            "message": f"成功加载 {filename},包含 {node_count} 个节点"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"加载失败: {str(e)}"
        }


def update_workflow_node(
    filename: str,
    node_id: str,
    updates: Dict,
    output_dir: str = "output"
) -> Dict:
    """
    工具 7: 更新工作流中的特定节点

    Args:
        filename: 文件名
        node_id: 要更新的节点 ID
        updates: 要更新的字段和值
        output_dir: 输出目录 (默认: "output")

    Returns:
        dict: 更新结果
    """
    try:
        if not filename.endswith('.json'):
            filename = f"{filename}.json"

        filepath = os.path.join(output_dir, filename)

        # 加载工作流
        with open(filepath, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        # 找到并更新节点
        found = False
        for node in workflow.get('nodes', []):
            if node['id'] == node_id:
                # 更新 data 字段
                if 'data' not in node:
                    node['data'] = {}
                node['data'].update(updates)
                found = True
                break

        if not found:
            return {
                "success": False,
                "error": f"节点 {node_id} 不存在",
                "message": f"未找到节点 {node_id}"
            }

        # 保存更新后的工作流
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "filepath": filepath,
            "node_id": node_id,
            "updates": updates,
            "message": f"成功更新节点 {node_id}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"更新失败: {str(e)}"
        }


def add_node_to_workflow(
    filename: str,
    node_type: str,
    config: Dict,
    after_node_id: Optional[str] = None,
    output_dir: str = "output"
) -> Dict:
    """
    工具 8: 向工作流添加新节点

    Args:
        filename: 文件名
        node_type: 节点类型 (textReply, captureUserReply, etc.)
        config: 节点配置
        after_node_id: 在哪个节点之后添加 (可选)
        output_dir: 输出目录 (默认: "output")

    Returns:
        dict: 添加结果
    """
    try:
        if not filename.endswith('.json'):
            filename = f"{filename}.json"

        filepath = os.path.join(output_dir, filename)

        # 加载工作流
        with open(filepath, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        # 重建 Workflow 对象
        wf = Workflow(
            workflow.get('flow_name', 'updated_workflow'),
            workflow.get('flow_description', ''),
            lang='zh'
        )
        wf.nodes = workflow.get('nodes', [])
        wf.edges = workflow.get('edges', [])
        wf.variables = workflow.get('variables', [])

        # 根据类型添加节点
        new_block_id = None
        if node_type == 'textReply':
            new_block_id = wf.add_text_reply(
                text=config.get('text', ''),
                title=config.get('title', 'New Reply'),
                auto_connect=False
            )
        elif node_type == 'captureUserReply':
            new_block_id = wf.add_capture_user_reply(
                variable_name=config.get('variable_name', 'new_var'),
                description=config.get('description', ''),
                title=config.get('title', 'New Capture'),
                auto_connect=False
            )
        elif node_type == 'llmVariableAssignment':
            new_block_id = wf.add_llm_variable_assignment(
                prompt_template=config.get('prompt', ''),
                variable_assign=config.get('variable_assign', 'extracted'),
                title=config.get('title', 'New LLM Assignment'),
                auto_connect=False
            )
        elif node_type == 'llMReply':
            new_block_id = wf.add_llm_reply(
                prompt_template=config.get('prompt', ''),
                title=config.get('title', 'New LLM Reply'),
                auto_connect=False
            )

        if new_block_id is None:
            return {
                "success": False,
                "error": f"不支持的节点类型: {node_type}",
                "message": f"节点类型 {node_type} 不支持"
            }

        # 如果指定了 after_node_id，创建连接
        if after_node_id:
            wf.connect_nodes(after_node_id, new_block_id)

        # 保存
        wf.save(filepath)

        return {
            "success": True,
            "filepath": filepath,
            "new_node_id": new_block_id,
            "message": f"成功添加节点 {new_block_id}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"添加节点失败: {str(e)}"
        }


def delete_node_from_workflow(
    filename: str,
    node_id: str,
    output_dir: str = "output"
) -> Dict:
    """
    工具 9: 从工作流删除节点

    Args:
        filename: 文件名
        node_id: 要删除的节点 ID
        output_dir: 输出目录 (默认: "output")

    Returns:
        dict: 删除结果
    """
    try:
        if not filename.endswith('.json'):
            filename = f"{filename}.json"

        filepath = os.path.join(output_dir, filename)

        # 加载工作流
        with open(filepath, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        # 删除节点
        original_count = len(workflow.get('nodes', []))
        workflow['nodes'] = [n for n in workflow.get('nodes', []) if n['id'] != node_id]

        # 删除相关的边
        workflow['edges'] = [e for e in workflow.get('edges', [])
                           if e['source'] != node_id and e['target'] != node_id]

        if len(workflow['nodes']) == original_count:
            return {
                "success": False,
                "error": f"节点 {node_id} 不存在",
                "message": f"未找到节点 {node_id}"
            }

        # 保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "filepath": filepath,
            "deleted_node_id": node_id,
            "message": f"成功删除节点 {node_id}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"删除节点失败: {str(e)}"
        }


# ============ 工具定义 (for Claude SDK) ============

TOOLS = [
    {
        "name": "parse_workflow_description",
        "description": "解析自然语言描述为结构化的工作流步骤。支持中英文描述,自动识别节点类型和提取变量。",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "用户的自然语言描述,如'询问姓名,获取姓名,发送感谢'"
                },
                "lang": {
                    "type": "string",
                    "description": "语言代码 (zh, en, auto)",
                    "enum": ["zh", "en", "auto"],
                    "default": "auto"
                }
            },
            "required": ["description"]
        }
    },
    {
        "name": "generate_workflow",
        "description": "根据解析后的步骤生成完整的 chatflow JSON 并自动保存到 Supabase Storage。无需再调用 save_workflow_to_file。返回文件名和存储 URL。",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_name": {
                    "type": "string",
                    "description": "工作流名称 (同时作为文件名),如 'customer_info'"
                },
                "steps": {
                    "type": "array",
                    "description": "步骤列表 (from parse_workflow_description)",
                    "items": {"type": "object"}
                },
                "description": {
                    "type": "string",
                    "description": "工作流描述 (可选)",
                    "default": ""
                },
                "lang": {
                    "type": "string",
                    "description": "语言代码 (en, zh)",
                    "enum": ["en", "zh"],
                    "default": "en"
                },
                "user_id": {
                    "type": "string",
                    "description": "用户 ID,用于隔离存储",
                    "default": "public"
                }
            },
            "required": ["workflow_name", "steps"]
        }
    },
    {
        "name": "validate_workflow",
        "description": "验证 workflow JSON 的结构是否正确,检查必需字段、节点完整性等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "object",
                    "description": "完整的 workflow JSON"
                }
            },
            "required": ["workflow"]
        }
    },
    {
        "name": "save_workflow_to_file",
        "description": "保存 workflow JSON 到文件系统,默认保存到 output/ 目录。",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "object",
                    "description": "完整的 workflow JSON"
                },
                "filename": {
                    "type": "string",
                    "description": "文件名,如 'my_workflow.json' 或 'my_workflow'"
                },
                "output_dir": {
                    "type": "string",
                    "description": "输出目录路径",
                    "default": "output"
                }
            },
            "required": ["workflow", "filename"]
        }
    },
    {
        "name": "list_workflow_files",
        "description": "列出所有已保存的工作流文件。",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_dir": {
                    "type": "string",
                    "description": "输出目录路径",
                    "default": "output"
                }
            },
            "required": []
        }
    },
    {
        "name": "load_workflow_from_file",
        "description": "从文件加载已有的工作流,返回工作流内容和摘要信息。用于查看或修改现有工作流。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "文件名,如 'my_workflow.json'"
                },
                "output_dir": {
                    "type": "string",
                    "description": "输出目录路径",
                    "default": "output"
                }
            },
            "required": ["filename"]
        }
    },
    {
        "name": "update_workflow_node",
        "description": "更新工作流中特定节点的配置。用于修改节点的文本、变量名、提示词等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "工作流文件名"
                },
                "node_id": {
                    "type": "string",
                    "description": "要更新的节点 ID"
                },
                "updates": {
                    "type": "object",
                    "description": "要更新的字段和值,如 {\"text\": \"新内容\"}"
                },
                "output_dir": {
                    "type": "string",
                    "description": "输出目录路径",
                    "default": "output"
                }
            },
            "required": ["filename", "node_id", "updates"]
        }
    },
    {
        "name": "add_node_to_workflow",
        "description": "向现有工作流添加新节点。支持 textReply、captureUserReply、llmVariableAssignment、llMReply 类型。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "工作流文件名"
                },
                "node_type": {
                    "type": "string",
                    "description": "节点类型",
                    "enum": ["textReply", "captureUserReply", "llmVariableAssignment", "llMReply"]
                },
                "config": {
                    "type": "object",
                    "description": "节点配置,如 {\"text\": \"内容\", \"title\": \"标题\"}"
                },
                "after_node_id": {
                    "type": "string",
                    "description": "在哪个节点之后添加并连接 (可选)"
                },
                "output_dir": {
                    "type": "string",
                    "description": "输出目录路径",
                    "default": "output"
                }
            },
            "required": ["filename", "node_type", "config"]
        }
    },
    {
        "name": "delete_node_from_workflow",
        "description": "从工作流中删除指定节点及其相关连线。",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "工作流文件名"
                },
                "node_id": {
                    "type": "string",
                    "description": "要删除的节点 ID"
                },
                "output_dir": {
                    "type": "string",
                    "description": "输出目录路径",
                    "default": "output"
                }
            },
            "required": ["filename", "node_id"]
        }
    }
]


def execute_tool(tool_name: str, tool_input: Dict) -> Dict:
    """
    工具路由器 - 根据工具名称调用对应的函数

    Args:
        tool_name: 工具名称
        tool_input: 工具输入参数

    Returns:
        dict: 工具执行结果
    """
    if tool_name == "parse_workflow_description":
        return parse_workflow_description(**tool_input)

    elif tool_name == "generate_workflow":
        return generate_workflow(**tool_input)

    elif tool_name == "validate_workflow":
        return validate_workflow(**tool_input)

    elif tool_name == "save_workflow_to_file":
        return save_workflow_to_file(**tool_input)

    elif tool_name == "list_workflow_files":
        return list_workflow_files(**tool_input)

    elif tool_name == "load_workflow_from_file":
        return load_workflow_from_file(**tool_input)

    elif tool_name == "update_workflow_node":
        return update_workflow_node(**tool_input)

    elif tool_name == "add_node_to_workflow":
        return add_node_to_workflow(**tool_input)

    elif tool_name == "delete_node_from_workflow":
        return delete_node_from_workflow(**tool_input)

    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
            "message": f"未知工具: {tool_name}"
        }
