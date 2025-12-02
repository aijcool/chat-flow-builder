// Workflow 相关类型定义

export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface Workflow {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Variable {
  name: string;
  description: string;
  value?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt?: Date;
}

export interface NodeConfig {
  type: string;
  title: string;
  content?: string;
  variableName?: string;
  prompt?: string;
  conditions?: ConditionConfig[];
}

export interface ConditionConfig {
  conditionName: string;
  logicalOperator: string;
  conditions: {
    conditionType: string;
    comparisonOperator: string;
    conditionValue: string;
    conditionVariable: string;
  }[];
}
