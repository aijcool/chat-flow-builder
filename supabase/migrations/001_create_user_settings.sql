-- 创建用户设置表
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    api_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- 启用 RLS
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- 创建策略：只允许服务角色访问
CREATE POLICY "Service role can do everything" ON user_settings
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- 创建对话历史表
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_workflow_name ON conversations(workflow_name);

-- 启用 RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- 创建策略
CREATE POLICY "Service role can do everything" ON conversations
    FOR ALL
    USING (true)
    WITH CHECK (true);
