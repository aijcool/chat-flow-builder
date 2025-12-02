"use client"

import { useCallback, useEffect, useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeMouseHandler,
  BackgroundVariant,
  MarkerType,
  ConnectionMode,
} from 'reactflow'
import 'reactflow/dist/style.css'

import { useWorkflowStore } from '@/hooks/useWorkflowStore'
import { CustomNode } from './CustomNode'
import { FlowToolbar } from './FlowToolbar'

const nodeTypes = {
  custom: CustomNode,
}

// 默认边样式
const defaultEdgeOptions = {
  type: 'smoothstep',
  animated: false,
  style: { stroke: '#94a3b8', strokeWidth: 2 },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    width: 15,
    height: 15,
    color: '#94a3b8',
  },
}

export function FlowCanvas() {
  const {
    nodes: storeNodes,
    edges: storeEdges,
    setNodes: setStoreNodes,
    setEdges: setStoreEdges,
    setSelectedNode,
    currentFile
  } = useWorkflowStore()

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // 同步 store 数据到本地状态
  useEffect(() => {
    setNodes(storeNodes)
  }, [storeNodes, setNodes])

  useEffect(() => {
    setEdges(storeEdges)
  }, [storeEdges, setEdges])

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds))
    },
    [setEdges]
  )

  const onNodeClick: NodeMouseHandler = useCallback(
    (_, node) => {
      setSelectedNode(node)
    },
    [setSelectedNode]
  )

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [setSelectedNode])

  // 节点变化时同步到 store
  useEffect(() => {
    if (nodes.length > 0) {
      setStoreNodes(nodes)
    }
  }, [nodes, setStoreNodes])

  useEffect(() => {
    if (edges.length > 0) {
      setStoreEdges(edges)
    }
  }, [edges, setStoreEdges])

  // 为边添加默认样式
  const styledEdges = useMemo(() => {
    return edges.map(edge => ({
      ...edge,
      type: edge.type || 'smoothstep',
      style: edge.style || { stroke: '#94a3b8', strokeWidth: 2 },
      markerEnd: edge.markerEnd || {
        type: MarkerType.ArrowClosed,
        width: 15,
        height: 15,
        color: '#94a3b8',
      },
    }))
  }, [edges])

  return (
    <div className="h-full w-full relative">
      <FlowToolbar />
      <ReactFlow
        nodes={nodes}
        edges={styledEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        connectionMode={ConnectionMode.Loose}
        fitView
        attributionPosition="bottom-left"
        className="bg-background"
      >
        <Controls className="bg-background border rounded-lg shadow-sm" />
        <MiniMap
          className="bg-muted border rounded-lg shadow-sm"
          nodeColor={(node) => {
            switch (node.data?.type) {
              case 'textReply':
                return '#3b82f6'
              case 'captureUserReply':
                return '#10b981'
              case 'condition':
                return '#f59e0b'
              case 'llmVariableAssignment':
                return '#8b5cf6'
              case 'llMReply':
                return '#ec4899'
              default:
                return '#6b7280'
            }
          }}
        />
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
      </ReactFlow>

      {!currentFile && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/80">
          <div className="text-center text-muted-foreground">
            <p className="text-lg mb-2">未加载工作流</p>
            <p className="text-sm">请通过对话生成工作流，或从列表中选择一个文件</p>
          </div>
        </div>
      )}
    </div>
  )
}
