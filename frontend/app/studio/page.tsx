"use client"

import { useState } from 'react'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { ConversationHistory } from '@/components/chat/ConversationHistory'
import { FlowCanvas } from '@/components/flow/FlowCanvas'
import { NodeEditor } from '@/components/flow/NodeEditor'
import { VariablesPanel } from '@/components/flow/VariablesPanel'

interface Conversation {
  id: string
  workflow_name: string
  created_at: string
  updated_at: string
}

export default function StudioPage() {
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)

  return (
    <main className="h-screen flex">
      {/* 左侧历史对话列表 */}
      <div className="w-[220px] border-r flex-shrink-0 flex flex-col">
        {/* 标题 */}
        <div className="px-4 py-3 border-b">
          <h1 className="text-lg font-semibold">Chatflow Tailor</h1>
          <p className="text-xs text-muted-foreground">与 Agent 对话生成工作流</p>
        </div>
        <ConversationHistory
          onSelectConversation={setCurrentConversation}
          currentConversationId={currentConversation?.id || null}
        />
      </div>

      {/* 中间聊天面板 */}
      <div className="w-[400px] border-r flex-shrink-0">
        <ChatPanel />
      </div>

      {/* 右侧画布 */}
      <div className="flex-1 relative">
        <FlowCanvas />
        <NodeEditor />
        <VariablesPanel />
      </div>
    </main>
  )
}
