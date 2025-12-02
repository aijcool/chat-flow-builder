"use client"

import { useState, useEffect } from 'react'
import { X, Save } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { useWorkflowStore } from '@/hooks/useWorkflowStore'
import { updateNode } from '@/lib/api'

export function NodeEditor() {
  const { selectedNode, setSelectedNode, updateNodeData, currentFile } = useWorkflowStore()
  const [formData, setFormData] = useState<Record<string, unknown>>({})

  useEffect(() => {
    if (selectedNode) {
      setFormData(selectedNode.data || {})
    }
  }, [selectedNode])

  if (!selectedNode) return null

  const handleChange = (key: string, value: unknown) => {
    setFormData(prev => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    if (!selectedNode || !currentFile) return

    updateNodeData(selectedNode.id, formData)

    try {
      await updateNode(currentFile, selectedNode.id, formData)
    } catch (error) {
      console.error('Failed to save node:', error)
    }
  }

  const handleClose = () => {
    setSelectedNode(null)
  }

  const nodeType = formData.type as string

  return (
    <Card className="absolute right-4 top-4 w-80 z-20 shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">编辑节点</CardTitle>
        <Button variant="ghost" size="icon" onClick={handleClose}>
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4 space-y-4 max-h-[500px] overflow-y-auto">
        {/* 通用字段 */}
        <div className="space-y-2">
          <Label>标题</Label>
          <Input
            value={(formData.title as string) || ''}
            onChange={(e) => handleChange('title', e.target.value)}
            placeholder="节点标题"
          />
        </div>

        {/* textReply 类型 */}
        {nodeType === 'textReply' && (
          <div className="space-y-2">
            <Label>回复内容</Label>
            <Textarea
              value={(formData.content as string) || ''}
              onChange={(e) => handleChange('content', e.target.value)}
              placeholder="输入回复文本内容..."
              className="min-h-[100px]"
            />
          </div>
        )}

        {/* captureUserReply 类型 */}
        {nodeType === 'captureUserReply' && (
          <>
            <div className="space-y-2">
              <Label>变量名称</Label>
              <Input
                value={(formData.variableName as string) || ''}
                onChange={(e) => handleChange('variableName', e.target.value)}
                placeholder="user_input"
              />
            </div>
            <div className="space-y-2">
              <Label>变量描述</Label>
              <Input
                value={(formData.variableDescription as string) || ''}
                onChange={(e) => handleChange('variableDescription', e.target.value)}
                placeholder="用户输入的内容"
              />
            </div>
          </>
        )}

        {/* llmVariableAssignment 类型 */}
        {nodeType === 'llmVariableAssignment' && (
          <>
            <div className="space-y-2">
              <Label>提示词模板</Label>
              <Textarea
                value={(formData.prompt as string) || ''}
                onChange={(e) => handleChange('prompt', e.target.value)}
                placeholder="请从 {{variable}} 中提取..."
                className="min-h-[100px]"
              />
            </div>
            <div className="space-y-2">
              <Label>输出变量</Label>
              <Input
                value={(formData.variableAssign as string) || ''}
                onChange={(e) => handleChange('variableAssign', e.target.value)}
                placeholder="extracted_data"
              />
            </div>
          </>
        )}

        {/* llMReply 类型 */}
        {nodeType === 'llMReply' && (
          <div className="space-y-2">
            <Label>提示词模板</Label>
            <Textarea
              value={(formData.prompt as string) || ''}
              onChange={(e) => handleChange('prompt', e.target.value)}
              placeholder="请根据用户的 {{variable}} 回答..."
              className="min-h-[100px]"
            />
          </div>
        )}

        {/* condition 类型 */}
        {nodeType === 'condition' && (
          <div className="space-y-2">
            <Label>条件说明</Label>
            <p className="text-xs text-muted-foreground">
              条件节点的详细配置需要在 JSON 中编辑
            </p>
            <Textarea
              value={JSON.stringify(formData.conditions || [], null, 2)}
              onChange={(e) => {
                try {
                  handleChange('conditions', JSON.parse(e.target.value))
                } catch {
                  // ignore parse errors while typing
                }
              }}
              placeholder="[]"
              className="min-h-[150px] font-mono text-xs"
            />
          </div>
        )}

        {/* 节点 ID 显示 */}
        <div className="pt-2 border-t">
          <p className="text-xs text-muted-foreground">
            节点 ID: {selectedNode.id}
          </p>
        </div>

        {/* 保存按钮 */}
        <Button onClick={handleSave} className="w-full">
          <Save className="h-4 w-4 mr-2" />
          保存修改
        </Button>
      </CardContent>
    </Card>
  )
}
