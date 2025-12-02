"use client"

import { useState, useEffect } from 'react'
import { MessageSquare, Plus, Trash2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { useAuth, useUser, UserButton } from '@clerk/nextjs'
import { UserSettingsDialog } from '@/components/settings/UserSettingsDialog'

interface Conversation {
  id: string
  workflow_name: string
  created_at: string
  updated_at: string
}

interface ConversationHistoryProps {
  onSelectConversation: (conversation: Conversation | null) => void
  currentConversationId: string | null
}

export function ConversationHistory({
  onSelectConversation,
  currentConversationId
}: ConversationHistoryProps) {
  const { userId } = useAuth()
  const { user } = useUser()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)

  // 加载对话历史
  useEffect(() => {
    if (userId) {
      loadConversations()
    }
  }, [userId])

  const loadConversations = async () => {
    if (!userId) return
    try {
      setLoading(true)
      const response = await fetch(`/api/conversations?user_id=${encodeURIComponent(userId)}`)
      if (response.ok) {
        const data = await response.json()
        setConversations(data.conversations || [])
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleNewConversation = () => {
    onSelectConversation(null)
  }

  const handleDeleteConversation = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation()
    if (!userId) return

    try {
      await fetch(`/api/conversations/${conversationId}?user_id=${encodeURIComponent(userId)}`, {
        method: 'DELETE'
      })
      setConversations(prev => prev.filter(c => c.id !== conversationId))
      if (currentConversationId === conversationId) {
        onSelectConversation(null)
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) return '今天'
    if (days === 1) return '昨天'
    if (days < 7) return `${days}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="flex flex-col h-full bg-muted/30">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-3 border-b">
        <span className="text-sm font-medium text-muted-foreground">历史对话</span>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={handleNewConversation}
          title="新建对话"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Conversation List */}
      <ScrollArea className="flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-8 px-4">
            <MessageSquare className="h-8 w-8 mx-auto mb-2 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">暂无对话记录</p>
            <p className="text-xs text-muted-foreground/70 mt-1">开始一个新对话吧</p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onSelectConversation(conversation)}
                className={cn(
                  "group flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors",
                  currentConversationId === conversation.id
                    ? "bg-primary/10 text-primary"
                    : "hover:bg-muted"
                )}
              >
                <MessageSquare className="h-4 w-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {conversation.workflow_name || '未命名工作流'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(conversation.updated_at)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => handleDeleteConversation(e, conversation.id)}
                >
                  <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Bottom - User Profile & Settings */}
      <div className="border-t px-3 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <UserButton afterSignOutUrl="/" />
          <span className="text-sm text-foreground truncate max-w-[100px]">
            {user?.firstName || user?.username || '用户'}
          </span>
        </div>
        <UserSettingsDialog />
      </div>
    </div>
  )
}
