"use client"

import { useState } from 'react'
import { LayoutGrid, Plus, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useWorkflowStore } from '@/hooks/useWorkflowStore'
import { autoLayout } from '@/lib/api'
import { useAuth } from '@clerk/nextjs'

// 直连后端 URL
const BACKEND_DIRECT = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api'

export function FlowToolbar() {
  const { userId } = useAuth()
  const [isAddNodeOpen, setIsAddNodeOpen] = useState(false)
  const [newNodeType, setNewNodeType] = useState('textReply')
  const [newNodeTitle, setNewNodeTitle] = useState('')

  const {
    currentFile,
    nodes,
    edges,
    setNodes,
    addNode
  } = useWorkflowStore()

  // 自动布局
  const handleAutoLayout = async () => {
    if (!currentFile) return
    try {
      const data = await autoLayout(currentFile, userId || 'public')
      setNodes(data.nodes)
    } catch (error) {
      console.error('Failed to auto layout:', error)
    }
  }

  // 下载 JSON 文件
  const handleDownloadJSON = async () => {
    if (!currentFile) return

    try {
      // 直接从 Supabase 获取原始 JSON
      const response = await fetch(
        `${BACKEND_DIRECT}/workflows/${encodeURIComponent(currentFile)}/download?user_id=${encodeURIComponent(userId || 'public')}`
      )

      if (!response.ok) {
        throw new Error('Failed to download workflow')
      }

      const data = await response.json()

      // 创建下载链接
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = currentFile
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download workflow:', error)
    }
  }

  // 添加节点
  const handleAddNode = () => {
    if (!newNodeTitle.trim()) return

    const newNode = {
      id: `node_${Date.now()}`,
      type: 'custom',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        type: newNodeType,
        title: newNodeTitle,
      }
    }

    addNode(newNode)
    setIsAddNodeOpen(false)
    setNewNodeTitle('')
  }

  return (
    <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
      {/* 当前文件名显示 */}
      {currentFile && (
        <Badge variant="secondary" className="px-3 py-1.5 text-sm font-medium">
          {currentFile}
        </Badge>
      )}

      {/* 下载 JSON */}
      <Button
        variant="outline"
        size="icon"
        onClick={handleDownloadJSON}
        disabled={!currentFile}
        title="下载 JSON"
      >
        <Download className="h-4 w-4" />
      </Button>

      {/* 自动布局 */}
      <Button
        variant="outline"
        size="icon"
        onClick={handleAutoLayout}
        disabled={!currentFile}
        title="自动布局"
      >
        <LayoutGrid className="h-4 w-4" />
      </Button>

      {/* 添加节点 */}
      <Dialog open={isAddNodeOpen} onOpenChange={setIsAddNodeOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="icon" disabled={!currentFile} title="添加节点">
            <Plus className="h-4 w-4" />
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加节点</DialogTitle>
            <DialogDescription>选择节点类型并输入名称</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>节点类型</Label>
              <Select value={newNodeType} onValueChange={setNewNodeType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="textReply">文本回复</SelectItem>
                  <SelectItem value="captureUserReply">获取用户输入</SelectItem>
                  <SelectItem value="condition">条件判断</SelectItem>
                  <SelectItem value="llmVariableAssignment">LLM变量提取</SelectItem>
                  <SelectItem value="llMReply">LLM回复</SelectItem>
                  <SelectItem value="code">代码</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>节点名称</Label>
              <Input
                value={newNodeTitle}
                onChange={(e) => setNewNodeTitle(e.target.value)}
                placeholder="输入节点名称"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddNodeOpen(false)}>取消</Button>
            <Button onClick={handleAddNode}>添加</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
