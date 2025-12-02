import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

const supabase = createClient(supabaseUrl, supabaseServiceKey)

// 获取单个对话详情
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get('user_id')

  if (!userId) {
    return NextResponse.json({ error: 'Missing user_id' }, { status: 400 })
  }

  try {
    const { data, error } = await supabase
      .from('conversations')
      .select('*')
      .eq('id', id)
      .eq('user_id', userId)
      .single()

    if (error) {
      throw error
    }

    return NextResponse.json({ conversation: data })
  } catch (error) {
    console.error('Failed to get conversation:', error)
    return NextResponse.json({ error: 'Failed to get conversation' }, { status: 500 })
  }
}

// 更新对话
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  try {
    const body = await request.json()
    const { user_id, workflow_name, messages } = body

    if (!user_id) {
      return NextResponse.json({ error: 'Missing user_id' }, { status: 400 })
    }

    const updateData: Record<string, unknown> = {
      updated_at: new Date().toISOString()
    }

    if (workflow_name !== undefined) {
      updateData.workflow_name = workflow_name
    }
    if (messages !== undefined) {
      updateData.messages = messages
    }

    const { error } = await supabase
      .from('conversations')
      .update(updateData)
      .eq('id', id)
      .eq('user_id', user_id)

    if (error) {
      throw error
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Failed to update conversation:', error)
    return NextResponse.json({ error: 'Failed to update conversation' }, { status: 500 })
  }
}

// 删除对话
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get('user_id')

  if (!userId) {
    return NextResponse.json({ error: 'Missing user_id' }, { status: 400 })
  }

  try {
    const { error } = await supabase
      .from('conversations')
      .delete()
      .eq('id', id)
      .eq('user_id', userId)

    if (error) {
      throw error
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Failed to delete conversation:', error)
    return NextResponse.json({ error: 'Failed to delete conversation' }, { status: 500 })
  }
}
