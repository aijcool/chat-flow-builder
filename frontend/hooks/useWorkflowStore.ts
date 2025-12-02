import { create } from 'zustand';
import { Node, Edge } from 'reactflow';
import { Variable } from '@/types';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Date;
}

// 工作流文件信息
interface WorkflowFile {
  name: string;
  url: string;
  created_at?: string;
}

interface WorkflowState {
  // Flow 数据
  nodes: Node[];
  edges: Edge[];
  variables: Variable[];

  // 聊天数据
  messages: ChatMessage[];
  isLoading: boolean;

  // 当前工作流文件
  currentFile: string | null;
  workflowFiles: WorkflowFile[];

  // 选中的节点
  selectedNode: Node | null;

  // Actions
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  setVariables: (variables: Variable[]) => void;
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setLoading: (loading: boolean) => void;
  setCurrentFile: (file: string | null) => void;
  setWorkflowFiles: (files: WorkflowFile[]) => void;
  setSelectedNode: (node: Node | null) => void;
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void;
  addNode: (node: Node) => void;
  addEdge: (edge: Edge) => void;
  removeNode: (nodeId: string) => void;
  removeEdge: (edgeId: string) => void;
  clearMessages: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  nodes: [],
  edges: [],
  variables: [],
  messages: [],
  isLoading: false,
  currentFile: null,
  workflowFiles: [],
  selectedNode: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setVariables: (variables) => set({ variables }),

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  setMessages: (messages) => set({ messages }),
  setLoading: (isLoading) => set({ isLoading }),
  setCurrentFile: (currentFile) => set({ currentFile }),
  setWorkflowFiles: (workflowFiles) => set({ workflowFiles }),
  setSelectedNode: (selectedNode) => set({ selectedNode }),

  updateNodeData: (nodeId, data) => set((state) => ({
    nodes: state.nodes.map(node =>
      node.id === nodeId
        ? { ...node, data: { ...node.data, ...data } }
        : node
    )
  })),

  addNode: (node) => set((state) => ({
    nodes: [...state.nodes, node]
  })),

  addEdge: (edge) => set((state) => ({
    edges: [...state.edges, edge]
  })),

  removeNode: (nodeId) => set((state) => ({
    nodes: state.nodes.filter(n => n.id !== nodeId),
    edges: state.edges.filter(e => e.source !== nodeId && e.target !== nodeId)
  })),

  removeEdge: (edgeId) => set((state) => ({
    edges: state.edges.filter(e => e.id !== edgeId)
  })),

  clearMessages: () => set({ messages: [] })
}));
