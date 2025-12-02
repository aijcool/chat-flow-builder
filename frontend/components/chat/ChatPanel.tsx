"use client"

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Loader2, FileJson } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useWorkflowStore } from '@/hooks/useWorkflowStore'
import { sendMessageSSE, resetConversation, SSECallbacks, loadWorkflow, getWorkflowFiles } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useAuth } from '@clerk/nextjs'

// 进度状态类型
interface ProgressStatus {
  status: string
  message: string
  loop?: number
}

// 工具调用状态类型
interface ToolStatus {
  name: string
  status: string
  message: string
  success?: boolean
}

export function ChatPanel() {
  const { userId } = useAuth()
  const [input, setInput] = useState('')
  const [progressStatus, setProgressStatus] = useState<ProgressStatus | null>(null)
  const [toolCalls, setToolCalls] = useState<ToolStatus[]>([])
  const cancelRef = useRef<(() => void) | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const {
    messages,
    isLoading,
    addMessage,
    setLoading,
    clearMessages,
    setNodes,
    setEdges,
    setVariables,
    setCurrentFile,
    setWorkflowFiles
  } = useWorkflowStore()

  // 点击文件名加载工作流到画布
  const handleFileClick = useCallback(async (filename: string) => {
    try {
      const data = await loadWorkflow(filename, userId || 'public')
      setNodes(data.nodes)
      setEdges(data.edges)
      setVariables(data.variables)
      setCurrentFile(filename)
      // 刷新文件列表
      const files = await getWorkflowFiles(userId || 'public')
      setWorkflowFiles(files)
    } catch (error) {
      console.error('Failed to load workflow:', error)
    }
  }, [setNodes, setEdges, setVariables, setCurrentFile, setWorkflowFiles, userId])

  // 渲染消息内容，将 .json 文件名变为可点击链接
  const renderMessageContent = useCallback((content: string) => {
    // 匹配 .json 文件名的正则 (支持中括号包围或独立的文件名)
    const filePattern = /\[?([a-zA-Z0-9_\-]+\.json)\]?/g
    const parts: (string | JSX.Element)[] = []
    let lastIndex = 0
    let match

    while ((match = filePattern.exec(content)) !== null) {
      // 添加匹配前的文本
      if (match.index > lastIndex) {
        parts.push(content.slice(lastIndex, match.index))
      }

      // 添加可点击的文件名
      const filename = match[1]
      parts.push(
        <button
          key={match.index}
          onClick={() => handleFileClick(filename)}
          className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary/10 hover:bg-primary/20 text-primary rounded transition-colors"
        >
          <FileJson className="h-3 w-3" />
          {filename}
        </button>
      )

      lastIndex = match.index + match[0].length
    }

    // 添加剩余文本
    if (lastIndex < content.length) {
      parts.push(content.slice(lastIndex))
    }

    return parts.length > 0 ? parts : content
  }, [handleFileClick])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()

    if (!input.trim() || isLoading) return

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input.trim(),
      createdAt: new Date()
    }

    addMessage(userMessage)
    setInput('')
    setLoading(true)
    setProgressStatus(null)
    setToolCalls([])

    // SSE 回调
    const callbacks: SSECallbacks = {
      onProgress: (data) => {
        setProgressStatus(data)
      },
      onTool: (data) => {
        setToolCalls(prev => {
          // 更新已有工具状态或添加新工具
          const existingIndex = prev.findIndex(t => t.name === data.name && t.status === 'calling')
          if (data.status === 'completed' && existingIndex !== -1) {
            const updated = [...prev]
            updated[existingIndex] = data
            return updated
          }
          return [...prev, data]
        })
      },
      onResult: (data) => {
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content: data.response,
          createdAt: new Date()
        }
        addMessage(assistantMessage)
        setLoading(false)
        setProgressStatus(null)
        setToolCalls([])
        cancelRef.current = null
      },
      onError: (error) => {
        console.error('SSE error:', error)
        addMessage({
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content: `抱歉，处理消息时出现错误: ${error}`,
          createdAt: new Date()
        })
        setLoading(false)
        setProgressStatus(null)
        setToolCalls([])
        cancelRef.current = null
      }
    }

    // 发送 SSE 请求
    cancelRef.current = sendMessageSSE(userMessage.content, callbacks, userId || 'public')
  }

  const handleReset = async () => {
    // 取消正在进行的 SSE 连接
    if (cancelRef.current) {
      cancelRef.current()
      cancelRef.current = null
    }
    setLoading(false)
    setProgressStatus(null)
    setToolCalls([])

    try {
      await resetConversation(userId || 'public')
      clearMessages()
    } catch (error) {
      console.error('Failed to reset conversation:', error)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <p className="mb-2">欢迎使用 Chatflow Tailor!</p>
              <p className="text-sm">描述您想要的对话流程，我会帮您生成。</p>
              <p className="text-sm mt-4">例如:</p>
              <p className="text-sm italic">"我想创建一个机票预订流程，先询问出发地和目的地..."</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex",
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  "max-w-[85%] rounded-lg px-4 py-2 text-sm",
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                )}
              >
                <div className="whitespace-pre-wrap">{renderMessageContent(message.content)}</div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg px-4 py-3 min-w-[200px]">
                {/* 进度状态 */}
                <div className="flex items-center gap-2 mb-2">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <span className="text-sm font-medium">
                    {progressStatus?.message || '连接中...'}
                  </span>
                </div>

                {/* 工具调用列表 */}
                {toolCalls.length > 0 && (
                  <div className="space-y-1 mt-2 pt-2 border-t border-border/50">
                    {toolCalls.map((tool, index) => (
                      <div key={index} className="flex items-center gap-2 text-xs text-muted-foreground">
                        {tool.status === 'calling' ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : tool.success !== false ? (
                          <span className="text-green-500">✓</span>
                        ) : (
                          <span className="text-red-500">✗</span>
                        )}
                        <span>{tool.name}</span>
                        {tool.status === 'completed' && (
                          <span className="text-muted-foreground/60">- {tool.message}</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="描述您想要的工作流..."
            className="min-h-[60px] max-h-[120px] resize-none"
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
            className="h-[60px] w-[60px]"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>

    </div>
  )
}
