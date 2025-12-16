"""
FastAPI 后端服务 - 为前端提供 API

功能:
1. 聊天 API - 与 ChatflowAgent 交互 (SSE 流式响应)
2. 工作流 API - 从 Supabase Storage 加载、保存工作流
3. 自动布局 API - 使用 dagre 算法布局节点
"""
import os
import json
import asyncio
import queue
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 加载 .env 文件
load_dotenv()

from ..agent.chatflow_agent import ChatflowAgent
from ..utils.config import get_config

# Supabase 配置
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = "workflows"

# 调试输出
print(f"[server.py] SUPABASE_URL = {SUPABASE_URL[:50] if SUPABASE_URL else 'NOT SET'}...")

# 线程池用于运行阻塞的 Agent 调用
executor = ThreadPoolExecutor(max_workers=4)

app = FastAPI(title="Chatflow Tailor API", version="1.0.0")

# CORS 配置 - 允许前端直接请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://chatflow-tailor.pages.dev",
        "https://*.chatflow-tailor.pages.dev",
        "https://chat-flow-builder.pages.dev",
        "https://*.chat-flow-builder.pages.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 按用户存储的 Agent 实例
user_agents: Dict[str, ChatflowAgent] = {}


def get_user_api_key(user_id: str) -> Optional[str]:
    """从 Supabase 获取用户的 API Key"""
    if not user_id or user_id == 'public':
        return None

    try:
        # 查询 user_settings 表
        url = f"{SUPABASE_URL}/rest/v1/user_settings"
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        params = {
            "user_id": f"eq.{user_id}",
            "select": "api_key"
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0].get('api_key')
    except Exception as e:
        print(f"[get_user_api_key] Error: {e}")

    return None


def get_agent(user_id: str = "public") -> ChatflowAgent:
    """获取或初始化用户的 Agent"""
    global user_agents

    # 先尝试获取用户的 API Key
    user_api_key = get_user_api_key(user_id) if user_id != "public" else None

    # 生成缓存 key (基于用户 ID 和是否有自定义 API Key)
    cache_key = f"{user_id}:{bool(user_api_key)}"

    if cache_key not in user_agents:
        if user_api_key:
            # 使用用户的 API Key
            print(f"[get_agent] Using user API key for {user_id}")
            user_agents[cache_key] = ChatflowAgent(
                api_key=user_api_key,
                base_url="https://api.moonshot.cn/anthropic",  # Kimi API 兼容端点
                user_id=user_id
            )
        else:
            # 使用系统默认 API Key
            print(f"[get_agent] Using system API key for {user_id}")
            config = get_config()
            user_agents[cache_key] = ChatflowAgent(
                api_key=config.api_key,
                base_url=config.base_url,
                user_id=user_id
            )

    return user_agents[cache_key]


def reset_agent(user_id: str = "public"):
    """重置用户的 Agent（当 API Key 更新时调用）"""
    global user_agents
    # 删除该用户的所有缓存 Agent
    keys_to_remove = [k for k in user_agents if k.startswith(f"{user_id}:")]
    for key in keys_to_remove:
        del user_agents[key]


# ============ Pydantic 模型 ============

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class NodePosition(BaseModel):
    x: float
    y: float


class NodeData(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    variableName: Optional[str] = None
    prompt: Optional[str] = None


class AddNodeRequest(BaseModel):
    type: str
    position: NodePosition
    config: Dict[str, Any]


class AddEdgeRequest(BaseModel):
    source: str
    target: str


class UpdateNodeRequest(BaseModel):
    data: Dict[str, Any]


class WorkflowSaveRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


# ============ 聊天 API ============

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送消息给 Agent (传统 HTTP 模式，保留兼容)"""
    try:
        agent = get_agent()
        # 在线程池中运行阻塞的 Agent 调用，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, agent.chat, request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/stream")
async def chat_stream(
    message: str = Query(..., description="用户消息"),
    user_id: str = Query("public", description="用户 ID")
):
    """
    SSE 流式聊天 API

    返回 Server-Sent Events 流:
    - event: progress - 进度更新
    - event: tool - 工具调用信息
    - event: result - 最终结果
    - event: error - 错误信息
    """

    # 用于线程间通信的队列 (线程安全)
    event_queue: queue.Queue = queue.Queue()

    def progress_callback(event_type: str, data: Dict[str, Any]):
        """进度回调函数，由 Agent 调用"""
        event_queue.put({
            "type": event_type,
            "data": data
        })

    def run_agent():
        """在线程中运行 Agent"""
        try:
            agent = get_agent(user_id)
            # 设置进度回调
            agent.set_progress_callback(progress_callback)

            # 发送开始事件
            progress_callback("progress", {"status": "started", "message": "开始处理..."})

            # 运行 Agent
            response = agent.chat(message)

            # 如果响应过长(可能包含完整JSON)，提取文件名并简化
            import re
            if len(response) > 1000:
                # 提取所有 .json 文件名
                json_files = re.findall(r'[\w\-]+\.json', response)
                if json_files:
                    # 去重
                    unique_files = list(dict.fromkeys(json_files))
                    files_str = ', '.join(f'[{f}]' for f in unique_files)
                    response = f"✅ 已生成工作流 {files_str}\n\n点击文件名可在右侧画布查看和编辑。"
                else:
                    # 没有找到文件名，截断响应
                    response = response[:500] + "\n\n...(响应过长已截断)"

            # 发送结果
            progress_callback("result", {"response": response})

        except Exception as e:
            progress_callback("agent_error", {"error": str(e)})
        finally:
            # 发送结束信号
            event_queue.put(None)
            # 清除回调
            agent = get_agent(user_id)
            agent.set_progress_callback(None)

    async def event_generator():
        """生成 SSE 事件流"""
        loop = asyncio.get_event_loop()

        # 启动 Agent 线程
        thread = threading.Thread(target=run_agent)
        thread.start()

        try:
            while True:
                # 使用 run_in_executor 避免阻塞事件循环
                try:
                    event = await loop.run_in_executor(
                        None,
                        lambda: event_queue.get(timeout=0.5)
                    )
                except queue.Empty:
                    # 发送心跳保持连接
                    yield ": heartbeat\n\n"
                    continue

                if event is None:
                    # 结束信号
                    break

                # 格式化 SSE 事件
                event_type = event.get("type", "message")
                event_data = json.dumps(event.get("data", {}), ensure_ascii=False)
                # 调试日志
                print(f"[SSE] Sending event: {event_type}, data length: {len(event_data)}")
                # SSE 规范: 多行数据需要每行都以 "data: " 开头
                # 但为简化处理，我们确保 JSON 是单行的（json.dumps 默认不换行）
                # 额外安全措施：替换可能的换行符
                event_data = event_data.replace('\n', '\\n').replace('\r', '\\r')
                sse_message = f"event: {event_type}\ndata: {event_data}\n\n"
                print(f"[SSE] Message preview: {sse_message[:200]}...")
                yield sse_message

        finally:
            thread.join(timeout=1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        }
    )


@app.post("/api/chat/reset")
async def reset_chat(user_id: str = Query("public", description="用户 ID")):
    """重置对话历史"""
    try:
        agent = get_agent(user_id)
        agent.reset_conversation()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 工作流 API ============

@app.get("/api/workflows")
async def list_workflows(user_id: str = "public"):
    """获取 Supabase Storage 中的工作流文件列表"""
    try:
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
            return {"files": []}

        data = response.json()
        files = [
            {
                "name": item["name"],
                "url": f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{user_id}/{item['name']}",
                "created_at": item.get("created_at")
            }
            for item in data
            if item["name"].endswith('.json')
        ]

        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/{filename}")
async def get_workflow(filename: str, user_id: str = "public"):
    """从 Supabase Storage 加载工作流"""
    try:
        # 从 Supabase Storage 下载
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        data = response.json()

        # 转换为前端需要的格式
        nodes = convert_to_react_flow_nodes(data.get('nodes', []))
        edges = convert_to_react_flow_edges(data.get('edges', []))
        variables = extract_variables(data.get('nodes', []))

        return {
            "nodes": nodes,
            "edges": edges,
            "variables": variables,
            "storage_url": download_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/{filename}/download")
async def download_workflow(filename: str, user_id: str = "public"):
    """下载原始工作流 JSON（不做转换）"""
    try:
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/workflows/{filename}")
async def save_workflow(filename: str, request: WorkflowSaveRequest, user_id: str = "public"):
    """保存工作流到 Supabase Storage"""
    try:
        # 先从 Supabase 下载原始文件
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        original_data = response.json()

        # 更新位置
        node_positions = {n['id']: n['position'] for n in request.nodes}
        for node in original_data.get('nodes', []):
            if node['id'] in node_positions:
                node['position'] = node_positions[node['id']]

        # 上传回 Supabase (使用 upsert)
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "x-upsert": "true"
        }

        upload_response = requests.put(
            upload_url,
            headers=headers,
            data=json.dumps(original_data, ensure_ascii=False, indent=2)
        )

        if upload_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail="保存失败")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/workflows/{filename}/nodes/{node_id}")
async def update_node(filename: str, node_id: str, data: Dict[str, Any], user_id: str = "public"):
    """更新节点数据"""
    try:
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        workflow_data = response.json()

        # 找到并更新节点
        for node in workflow_data.get('nodes', []):
            if node['id'] == node_id:
                node['data'] = {**node.get('data', {}), **data}
                break

        # 上传回 Supabase
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "x-upsert": "true"
        }

        upload_response = requests.put(
            upload_url,
            headers=headers,
            data=json.dumps(workflow_data, ensure_ascii=False, indent=2)
        )

        if upload_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail="保存失败")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/{filename}/nodes")
async def add_node(filename: str, request: AddNodeRequest, user_id: str = "public"):
    """添加节点"""
    try:
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        workflow_data = response.json()

        # 创建新节点
        new_node_id = f"node_{len(workflow_data.get('nodes', []))}"
        new_node = {
            "id": new_node_id,
            "type": request.type,
            "position": {"x": request.position.x, "y": request.position.y},
            "data": request.config
        }

        workflow_data.setdefault('nodes', []).append(new_node)

        # 上传回 Supabase
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "x-upsert": "true"
        }

        upload_response = requests.put(
            upload_url,
            headers=headers,
            data=json.dumps(workflow_data, ensure_ascii=False, indent=2)
        )

        if upload_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail="保存失败")

        return {"node": new_node}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/workflows/{filename}/nodes/{node_id}")
async def delete_node(filename: str, node_id: str, user_id: str = "public"):
    """删除节点"""
    try:
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        workflow_data = response.json()

        # 删除节点
        workflow_data['nodes'] = [n for n in workflow_data.get('nodes', []) if n['id'] != node_id]
        # 删除相关边
        workflow_data['edges'] = [e for e in workflow_data.get('edges', [])
                                  if e['source'] != node_id and e['target'] != node_id]

        # 上传回 Supabase
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "x-upsert": "true"
        }

        upload_response = requests.put(
            upload_url,
            headers=headers,
            data=json.dumps(workflow_data, ensure_ascii=False, indent=2)
        )

        if upload_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail="保存失败")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/{filename}/edges")
async def add_edge(filename: str, request: AddEdgeRequest, user_id: str = "public"):
    """添加连线"""
    try:
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        workflow_data = response.json()

        new_edge = {
            "id": f"edge_{request.source}_{request.target}",
            "source": request.source,
            "target": request.target
        }

        workflow_data.setdefault('edges', []).append(new_edge)

        # 上传回 Supabase
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "x-upsert": "true"
        }

        upload_response = requests.put(
            upload_url,
            headers=headers,
            data=json.dumps(workflow_data, ensure_ascii=False, indent=2)
        )

        if upload_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail="保存失败")

        return {"edge": new_edge}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/workflows/{filename}/edges/{edge_id}")
async def delete_edge(filename: str, edge_id: str, user_id: str = "public"):
    """删除连线"""
    try:
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        workflow_data = response.json()

        workflow_data['edges'] = [e for e in workflow_data.get('edges', []) if e['id'] != edge_id]

        # 上传回 Supabase
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "x-upsert": "true"
        }

        upload_response = requests.put(
            upload_url,
            headers=headers,
            data=json.dumps(workflow_data, ensure_ascii=False, indent=2)
        )

        if upload_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail="保存失败")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/{filename}/layout")
async def auto_layout(filename: str, user_id: str = "public"):
    """自动布局节点"""
    try:
        storage_path = f"{user_id}/{filename}"
        download_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"

        response = requests.get(download_url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="文件不存在")

        workflow_data = response.json()

        nodes = workflow_data.get('nodes', [])
        edges = workflow_data.get('edges', [])

        # 使用简单层次布局
        laid_out_nodes = simple_hierarchical_layout(nodes, edges)

        # 更新节点位置
        node_positions = {n['id']: n['position'] for n in laid_out_nodes}
        for node in workflow_data['nodes']:
            if node['id'] in node_positions:
                node['position'] = node_positions[node['id']]

        # 上传回 Supabase
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "x-upsert": "true"
        }

        upload_response = requests.put(
            upload_url,
            headers=headers,
            data=json.dumps(workflow_data, ensure_ascii=False, indent=2)
        )

        if upload_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail="保存失败")

        return {"nodes": laid_out_nodes}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 辅助函数 ============

def convert_to_react_flow_nodes(nodes: List[Dict]) -> List[Dict]:
    """将工作流节点转换为 ReactFlow 格式"""
    react_flow_nodes = []

    for node in nodes:
        # 只处理功能节点，跳过 Block 节点
        node_type = node.get('type', '')
        if node_type == 'block':
            continue

        config = node.get('config', {})
        data = node.get('data', {})

        react_node = {
            "id": node['id'],
            "type": "custom",
            "position": node.get('position', {"x": 0, "y": 0}),
            "data": {
                "type": node_type,
                "title": config.get('title', data.get('title', data.get('name', ''))),
                **data
            }
        }

        # 根据节点类型提取特定数据
        if node_type == 'textReply':
            # 提取文本内容
            plain_text = config.get('plain_text', [])
            if plain_text and len(plain_text) > 0:
                react_node['data']['content'] = plain_text[0].get('text', '')

        elif node_type == 'captureUserReply':
            # 提取变量名
            react_node['data']['variableName'] = config.get('variable_assign', '')

        elif node_type == 'condition':
            # 提取条件列表
            conditions = config.get('if_else_conditions', [])
            react_node['data']['conditions'] = conditions

        elif node_type == 'llmVariableAssignment':
            # 提取 prompt 和变量名
            react_node['data']['prompt'] = config.get('prompt_template', '')
            react_node['data']['variableName'] = config.get('variable_assign', '')

        elif node_type == 'llMReply':
            # 提取 prompt
            react_node['data']['prompt'] = config.get('prompt_template', '')

        elif node_type == 'code':
            # 提取代码描述
            react_node['data']['content'] = config.get('desc', '') or '代码块'

        react_flow_nodes.append(react_node)

    return react_flow_nodes


def convert_to_react_flow_edges(edges: List[Dict]) -> List[Dict]:
    """将工作流边转换为 ReactFlow 格式"""
    return [
        {
            "id": edge.get('id', f"{edge['source']}-{edge['target']}"),
            "source": edge['source'],
            "target": edge['target'],
            "sourceHandle": edge.get('sourceHandle'),
            "targetHandle": edge.get('targetHandle')
        }
        for edge in edges
    ]


def extract_variables(nodes: List[Dict]) -> List[Dict]:
    """从节点中提取变量列表"""
    variables = []

    for node in nodes:
        config = node.get('config', {})
        data = node.get('data', {})
        node_type = node.get('type', '')

        # captureUserReply 节点
        if node_type == 'captureUserReply':
            var_name = config.get('variable_assign') or data.get('variableName') or data.get('variable_name')
            var_desc = data.get('variableDescription') or data.get('variable_description', '')
            title = config.get('title', data.get('title', ''))
            if var_name:
                variables.append({
                    "name": var_name,
                    "description": var_desc or f"用户输入 - {title}"
                })

        # llmVariableAssignment 节点
        elif node_type == 'llmVariableAssignment':
            var_name = config.get('variable_assign') or data.get('variableAssign') or data.get('variable_assign')
            title = config.get('title', data.get('title', ''))
            if var_name:
                variables.append({
                    "name": var_name,
                    "description": f"LLM 提取 - {title}"
                })

    return variables


def simple_hierarchical_layout(nodes: List[Dict], edges: List[Dict],
                                node_width: int = 220,
                                node_height: int = 100,
                                horizontal_spacing: int = 80,
                                vertical_spacing: int = 120) -> List[Dict]:
    """
    简单的层次布局算法
    基于拓扑排序将节点分层，然后在每层内水平排列
    """
    if not nodes:
        return nodes

    # 构建邻接表和入度表
    node_ids = {n['id'] for n in nodes}
    adjacency = defaultdict(list)
    in_degree = defaultdict(int)

    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        if source in node_ids and target in node_ids:
            adjacency[source].append(target)
            in_degree[target] += 1

    # 找出所有节点的入度
    for node in nodes:
        if node['id'] not in in_degree:
            in_degree[node['id']] = 0

    # 拓扑排序分层
    layers = []
    remaining = set(node_ids)

    while remaining:
        # 找出当前入度为 0 的节点作为新的一层
        current_layer = [nid for nid in remaining if in_degree[nid] == 0]

        if not current_layer:
            # 如果有环，随机选一个节点打破循环
            current_layer = [next(iter(remaining))]

        layers.append(current_layer)

        # 移除当前层的节点并更新入度
        for nid in current_layer:
            remaining.discard(nid)
            for neighbor in adjacency[nid]:
                in_degree[neighbor] -= 1

    # 计算每层的位置
    node_positions = {}
    y = 50

    for layer in layers:
        layer_width = len(layer) * (node_width + horizontal_spacing) - horizontal_spacing
        start_x = (1200 - layer_width) / 2  # 居中对齐，假设画布宽度 1200

        for i, nid in enumerate(layer):
            x = start_x + i * (node_width + horizontal_spacing)
            node_positions[nid] = {'x': x, 'y': y}

        y += node_height + vertical_spacing

    # 更新节点位置
    result = []
    for node in nodes:
        if node['id'] in node_positions:
            result.append({
                **node,
                'position': node_positions[node['id']]
            })
        else:
            result.append(node)

    return result


# ============ 启动 ============

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """运行服务器"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
