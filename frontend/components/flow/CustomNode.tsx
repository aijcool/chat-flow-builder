"use client"

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { cn } from '@/lib/utils'
import {
  MessageSquare,
  UserCheck,
  GitBranch,
  Code,
  Brain,
  Bot,
  Play
} from 'lucide-react'

const nodeTypeConfig: Record<string, { icon: React.ElementType; color: string; borderColor: string; label: string }> = {
  start: { icon: Play, color: 'bg-gray-500', borderColor: 'border-gray-500', label: '开始' },
  textReply: { icon: MessageSquare, color: 'bg-blue-500', borderColor: 'border-blue-500', label: '文本回复' },
  captureUserReply: { icon: UserCheck, color: 'bg-green-500', borderColor: 'border-green-500', label: '获取用户输入' },
  condition: { icon: GitBranch, color: 'bg-amber-500', borderColor: 'border-amber-500', label: '条件判断' },
  code: { icon: Code, color: 'bg-slate-500', borderColor: 'border-slate-500', label: '代码' },
  llmVariableAssignment: { icon: Brain, color: 'bg-violet-500', borderColor: 'border-violet-500', label: 'LLM变量提取' },
  llMReply: { icon: Bot, color: 'bg-pink-500', borderColor: 'border-pink-500', label: 'LLM回复' },
}

function CustomNodeComponent({ data, selected, isConnectable }: NodeProps) {
  const nodeType = data?.type || 'default'
  const config = nodeTypeConfig[nodeType] || { icon: MessageSquare, color: 'bg-gray-400', borderColor: 'border-gray-400', label: nodeType }
  const Icon = config.icon

  const title = data?.title || data?.name || config.label

  // 条件节点需要多个输出 handle
  const isConditionNode = nodeType === 'condition'

  return (
    <div
      className={cn(
        "min-w-[200px] max-w-[280px] rounded-lg border-2 bg-card shadow-md transition-all",
        config.borderColor,
        selected && "ring-2 ring-primary ring-offset-2 shadow-lg"
      )}
    >
      {/* 输入 Handle */}
      <Handle
        type="target"
        position={Position.Top}
        isConnectable={isConnectable}
        className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white !-top-1.5"
      />

      {/* Header */}
      <div className={cn("flex items-center gap-2 px-3 py-2 rounded-t-md text-white", config.color)}>
        <Icon className="h-4 w-4 flex-shrink-0" />
        <span className="text-sm font-medium truncate">{title}</span>
      </div>

      {/* Content */}
      <div className="px-3 py-2 text-xs text-muted-foreground min-h-[32px]">
        {data?.content && (
          <p className="line-clamp-2">{String(data.content).slice(0, 80)}{String(data.content).length > 80 ? '...' : ''}</p>
        )}
        {data?.variableName && (
          <p className="text-primary font-medium">变量: {data.variableName}</p>
        )}
        {data?.prompt && (
          <p className="line-clamp-2 italic text-muted-foreground/70">{String(data.prompt).slice(0, 60)}{String(data.prompt).length > 60 ? '...' : ''}</p>
        )}
        {/* 条件节点显示条件 */}
        {isConditionNode && data?.conditions && (
          <div className="space-y-1">
            {data.conditions.slice(0, 2).map((cond: any, idx: number) => (
              <p key={idx} className="text-primary/80 truncate">
                {cond.condition_name || cond.condition || `条件 ${idx + 1}`}
              </p>
            ))}
            {data.conditions.length > 2 && (
              <p className="text-muted-foreground/50">+{data.conditions.length - 2} 更多</p>
            )}
          </div>
        )}
        {!data?.content && !data?.variableName && !data?.prompt && !(isConditionNode && data?.conditions) && (
          <p className="text-muted-foreground/40">点击查看详情</p>
        )}
      </div>

      {/* 输出 Handle(s) */}
      {isConditionNode ? (
        <>
          {/* 条件节点：Yes/No 两个输出 */}
          <Handle
            type="source"
            position={Position.Bottom}
            id="yes"
            isConnectable={isConnectable}
            className="!w-3 !h-3 !bg-green-500 !border-2 !border-white !-bottom-1.5"
            style={{ left: '30%' }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="no"
            isConnectable={isConnectable}
            className="!w-3 !h-3 !bg-red-500 !border-2 !border-white !-bottom-1.5"
            style={{ left: '70%' }}
          />
          <div className="flex justify-between px-6 pb-1 text-[10px] text-muted-foreground">
            <span>是</span>
            <span>否</span>
          </div>
        </>
      ) : (
        <Handle
          type="source"
          position={Position.Bottom}
          isConnectable={isConnectable}
          className="!w-3 !h-3 !bg-slate-400 !border-2 !border-white !-bottom-1.5"
        />
      )}
    </div>
  )
}

export const CustomNode = memo(CustomNodeComponent)
