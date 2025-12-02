import { Variable } from '@/types';
import { Node, Edge } from 'reactflow';

// 代理 API 路径 (用于快速请求)
const API_BASE = '/api/backend';

// 直连后端 URL (用于长时间请求，绕过 Next.js 代理超时)
const BACKEND_DIRECT = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

// SSE 事件回调类型
export interface SSECallbacks {
  onProgress?: (data: { status: string; message: string; loop?: number }) => void;
  onTool?: (data: { name: string; status: string; message: string; success?: boolean }) => void;
  onResult?: (data: { response: string }) => void;
  onError?: (error: string) => void;
}

// 聊天 API - 使用 SSE 流式响应
export function sendMessageSSE(
  message: string,
  callbacks: SSECallbacks,
  userId: string = 'public'
): () => void {
  const url = `${BACKEND_DIRECT}/chat/stream?message=${encodeURIComponent(message)}&user_id=${encodeURIComponent(userId)}`;

  const eventSource = new EventSource(url);

  eventSource.addEventListener('progress', (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onProgress?.(data);
    } catch (e) {
      console.error('Failed to parse progress event:', e);
    }
  });

  eventSource.addEventListener('tool', (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onTool?.(data);
    } catch (e) {
      console.error('Failed to parse tool event:', e);
    }
  });

  eventSource.addEventListener('result', (event) => {
    try {
      console.log('SSE result event received, data length:', event.data?.length);
      if (!event.data || event.data.trim() === '') {
        throw new Error('Empty data received');
      }
      const data = JSON.parse(event.data);
      callbacks.onResult?.(data);
    } catch (e) {
      console.error('Failed to parse result event:', e, 'Raw data:', event.data?.substring(0, 500));
      // 如果解析失败，尝试直接显示完成消息
      callbacks.onResult?.({ response: '✅ 处理完成，请刷新文件列表查看生成的工作流' });
    } finally {
      eventSource.close();
    }
  });

  // 监听自定义 agent_error 事件 (避免与 EventSource 原生 error 事件冲突)
  eventSource.addEventListener('agent_error', (event) => {
    try {
      const data = JSON.parse(event.data);
      callbacks.onError?.(data.error || 'Unknown error');
    } catch (e) {
      callbacks.onError?.('处理错误');
    }
    eventSource.close();
  });

  eventSource.onerror = () => {
    if (eventSource.readyState === EventSource.CLOSED) {
      return;
    }
    callbacks.onError?.('连接断开');
    eventSource.close();
  };

  // 返回取消函数
  return () => {
    eventSource.close();
  };
}

// 旧版聊天 API - 保留兼容 (不推荐使用)
export async function sendMessage(message: string): Promise<string> {
  const response = await fetch(`${BACKEND_DIRECT}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.response;
}

// 重置对话 - 直连后端
export async function resetConversation(userId: string = 'public'): Promise<void> {
  await fetch(`${BACKEND_DIRECT}/chat/reset?user_id=${encodeURIComponent(userId)}`, { method: 'POST' });
}

// 工作流文件信息类型
export interface WorkflowFile {
  name: string;
  url: string;
  created_at?: string;
}

// 获取工作流列表 (从 Supabase Storage)
export async function getWorkflowFiles(userId: string = 'public'): Promise<WorkflowFile[]> {
  const response = await fetch(`${BACKEND_DIRECT}/workflows?user_id=${encodeURIComponent(userId)}`);
  const data = await response.json();
  return data.files || [];
}

// 加载工作流 (从 Supabase Storage)
export async function loadWorkflow(filename: string, userId: string = 'public'): Promise<{
  nodes: Node[];
  edges: Edge[];
  variables: Variable[];
  storage_url?: string;
}> {
  const response = await fetch(`${BACKEND_DIRECT}/workflows/${encodeURIComponent(filename)}?user_id=${encodeURIComponent(userId)}`);
  return response.json();
}

// 保存工作流
export async function saveWorkflow(filename: string, nodes: Node[], edges: Edge[], userId: string = 'public'): Promise<void> {
  await fetch(`${BACKEND_DIRECT}/workflows/${encodeURIComponent(filename)}?user_id=${encodeURIComponent(userId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nodes, edges })
  });
}

// 更新节点
export async function updateNode(
  filename: string,
  nodeId: string,
  data: Record<string, unknown>,
  userId: string = 'public'
): Promise<void> {
  await fetch(`${BACKEND_DIRECT}/workflows/${encodeURIComponent(filename)}/nodes/${nodeId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}

// 添加节点
export async function addNodeToWorkflow(
  filename: string,
  nodeType: string,
  position: { x: number; y: number },
  config: Record<string, unknown>,
  userId: string = 'public'
): Promise<{ node: Node }> {
  const response = await fetch(`${BACKEND_DIRECT}/workflows/${encodeURIComponent(filename)}/nodes?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: nodeType, position, config })
  });
  return response.json();
}

// 删除节点
export async function deleteNode(filename: string, nodeId: string, userId: string = 'public'): Promise<void> {
  await fetch(`${BACKEND_DIRECT}/workflows/${encodeURIComponent(filename)}/nodes/${nodeId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'DELETE'
  });
}

// 添加连线
export async function addEdgeToWorkflow(
  filename: string,
  source: string,
  target: string,
  userId: string = 'public'
): Promise<{ edge: Edge }> {
  const response = await fetch(`${BACKEND_DIRECT}/workflows/${encodeURIComponent(filename)}/edges?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, target })
  });
  return response.json();
}

// 删除连线
export async function deleteEdge(filename: string, edgeId: string, userId: string = 'public'): Promise<void> {
  await fetch(`${BACKEND_DIRECT}/workflows/${encodeURIComponent(filename)}/edges/${edgeId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'DELETE'
  });
}

// 自动布局
export async function autoLayout(filename: string, userId: string = 'public'): Promise<{ nodes: Node[] }> {
  const response = await fetch(`${BACKEND_DIRECT}/workflows/${encodeURIComponent(filename)}/layout?user_id=${encodeURIComponent(userId)}`, {
    method: 'POST'
  });
  return response.json();
}
