-- Fix history storage issue
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

CREATE INDEX IF NOT EXISTS idx_generated_documents_user_id ON generated_documents(user_id);
ALTER TABLE generated_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own documents" ON generated_documents
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own documents" ON generated_documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Service role can manage documents" ON generated_documents
    FOR ALL TO service_role USING (true) WITH CHECK (true);