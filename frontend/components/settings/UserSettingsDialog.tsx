"use client"

import { useState, useEffect } from 'react'
import { Settings, ExternalLink, Eye, EyeOff, Loader2, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useAuth } from '@clerk/nextjs'

interface UserSettings {
  apiKey?: string
}

export function UserSettingsDialog() {
  const { userId } = useAuth()
  const [open, setOpen] = useState(false)
  const [apiKey, setApiKey] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [loading, setLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle')

  // 加载用户设置
  useEffect(() => {
    if (open && userId) {
      loadSettings()
    }
  }, [open, userId])

  const loadSettings = async () => {
    if (!userId) return
    try {
      setLoading(true)
      const response = await fetch(`/api/user-settings?user_id=${encodeURIComponent(userId)}`)
      if (response.ok) {
        const data: UserSettings = await response.json()
        setApiKey(data.apiKey || '')
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!userId) return
    try {
      setSaveStatus('saving')
      const response = await fetch('/api/user-settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          apiKey
        })
      })

      if (response.ok) {
        setSaveStatus('saved')
        setTimeout(() => {
          setSaveStatus('idle')
          setOpen(false)
        }, 1000)
      }
    } catch (error) {
      console.error('Failed to save settings:', error)
      setSaveStatus('idle')
    }
  }

  // 遮罩 API Key 显示
  const maskedApiKey = apiKey
    ? apiKey.slice(0, 8) + '•'.repeat(Math.min(apiKey.length - 8, 20))
    : ''

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" title="设置">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>用户设置</DialogTitle>
          <DialogDescription>
            配置您的 API 密钥以使用 AI 功能
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="apiKey" className="flex items-center justify-between">
                <span>Kimi API Key</span>
                <a
                  href="https://platform.moonshot.cn/console/api-keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
                  获取 API Key
                  <ExternalLink className="h-3 w-3" />
                </a>
              </Label>
              <div className="relative">
                <Input
                  id="apiKey"
                  type={showApiKey ? 'text' : 'password'}
                  value={showApiKey ? apiKey : maskedApiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                  onClick={() => setShowApiKey(!showApiKey)}
                >
                  {showApiKey ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                API Key 将安全存储，用于调用 AI 服务生成工作流
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            取消
          </Button>
          <Button onClick={handleSave} disabled={saveStatus === 'saving'}>
            {saveStatus === 'saving' ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                保存中...
              </>
            ) : saveStatus === 'saved' ? (
              <>
                <Check className="mr-2 h-4 w-4" />
                已保存
              </>
            ) : (
              '保存'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
