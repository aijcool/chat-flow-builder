"use client"

import { Variable as VariableIcon, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useWorkflowStore } from '@/hooks/useWorkflowStore'
import { cn } from '@/lib/utils'

export function VariablesPanel() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const { variables, currentFile } = useWorkflowStore()

  if (!currentFile) return null

  return (
    <Card className={cn(
      "absolute left-4 bottom-4 z-10 w-64 transition-all",
      isCollapsed && "w-auto"
    )}>
      <CardHeader className="py-2 px-3 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <VariableIcon className="h-4 w-4 text-primary" />
          <CardTitle className="text-sm">变量列表</CardTitle>
          {!isCollapsed && (
            <Badge variant="secondary" className="text-xs">
              {variables.length}
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
        </Button>
      </CardHeader>

      {!isCollapsed && (
        <CardContent className="px-3 pb-3 pt-0">
          <ScrollArea className="max-h-[200px]">
            {variables.length === 0 ? (
              <p className="text-xs text-muted-foreground py-2">
                暂无变量
              </p>
            ) : (
              <div className="space-y-2">
                {variables.map((variable, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2 p-2 rounded-md bg-muted/50"
                  >
                    <code className="text-xs font-mono text-primary">
                      {`{{${variable.name}}}`}
                    </code>
                    <span className="text-xs text-muted-foreground flex-1">
                      {variable.description}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      )}
    </Card>
  )
}
