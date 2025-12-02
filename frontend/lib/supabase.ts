import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Workflow 存储相关函数
const BUCKET_NAME = 'workflows'

/**
 * 上传 workflow JSON 到 Supabase Storage
 */
export async function uploadWorkflow(
  filename: string,
  workflow: object,
  userId?: string
): Promise<{ url: string; path: string } | null> {
  try {
    const path = userId ? `${userId}/${filename}` : `public/${filename}`
    const content = JSON.stringify(workflow, null, 2)

    const { data, error } = await supabase.storage
      .from(BUCKET_NAME)
      .upload(path, content, {
        contentType: 'application/json',
        upsert: false // 不覆盖，如果存在会失败
      })

    if (error) {
      // 如果文件已存在，尝试添加序号
      if (error.message.includes('already exists')) {
        const baseName = filename.replace('.json', '')
        let counter = 1
        let newPath = `${userId ? `${userId}/` : 'public/'}${baseName}_${counter}.json`

        while (counter < 100) {
          const { data: retryData, error: retryError } = await supabase.storage
            .from(BUCKET_NAME)
            .upload(newPath, content, {
              contentType: 'application/json',
              upsert: false
            })

          if (!retryError) {
            const { data: urlData } = supabase.storage
              .from(BUCKET_NAME)
              .getPublicUrl(newPath)
            return { url: urlData.publicUrl, path: newPath }
          }

          counter++
          newPath = `${userId ? `${userId}/` : 'public/'}${baseName}_${counter}.json`
        }
      }
      console.error('Upload error:', error)
      return null
    }

    const { data: urlData } = supabase.storage
      .from(BUCKET_NAME)
      .getPublicUrl(path)

    return { url: urlData.publicUrl, path }
  } catch (err) {
    console.error('Upload workflow error:', err)
    return null
  }
}

/**
 * 从 URL 下载 workflow JSON
 */
export async function downloadWorkflow(url: string): Promise<object | null> {
  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error('Failed to fetch workflow')
    return await response.json()
  } catch (err) {
    console.error('Download workflow error:', err)
    return null
  }
}

/**
 * 从 Supabase Storage 路径下载 workflow
 */
export async function getWorkflowByPath(path: string): Promise<object | null> {
  try {
    const { data, error } = await supabase.storage
      .from(BUCKET_NAME)
      .download(path)

    if (error) {
      console.error('Download error:', error)
      return null
    }

    const text = await data.text()
    return JSON.parse(text)
  } catch (err) {
    console.error('Get workflow error:', err)
    return null
  }
}

/**
 * 列出用户的所有 workflow 文件
 */
export async function listUserWorkflows(userId: string): Promise<string[]> {
  try {
    const { data, error } = await supabase.storage
      .from(BUCKET_NAME)
      .list(userId, {
        limit: 100,
        sortBy: { column: 'created_at', order: 'desc' }
      })

    if (error) {
      console.error('List error:', error)
      return []
    }

    return data
      .filter(file => file.name.endsWith('.json'))
      .map(file => file.name)
  } catch (err) {
    console.error('List workflows error:', err)
    return []
  }
}
