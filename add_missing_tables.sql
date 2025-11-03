-- Add missing generated_documents table for document storage
CREATE TABLE IF NOT EXISTS generated_documents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    document_type TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    title TEXT,
    content TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_generated_documents_user_id ON generated_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_documents_created_at ON generated_documents(created_at DESC);

-- Enable RLS
ALTER TABLE generated_documents ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own documents" ON generated_documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents" ON generated_documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can manage documents" ON generated_documents
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Update existing user_history table to use UUID if needed
DO $$
BEGIN
    -- Check if user_history.user_id is INTEGER and convert to UUID
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_history' 
        AND column_name = 'user_id' 
        AND data_type = 'integer'
    ) THEN
        -- Drop existing foreign key constraint
        ALTER TABLE user_history DROP CONSTRAINT IF EXISTS user_history_user_id_fkey;
        
        -- Change column type to UUID
        ALTER TABLE user_history ALTER COLUMN user_id TYPE UUID USING user_id::text::uuid;
        
        -- Add new foreign key constraint
        ALTER TABLE user_history ADD CONSTRAINT user_history_user_id_fkey 
            FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;