-- Migration script for existing Legal Document Writer installations
-- Run this AFTER running supabase_schema.sql if you have existing data

-- Check if tables exist and create them if they don't
DO $$
BEGIN
    -- Check if user_history table exists
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_history') THEN
        RAISE NOTICE 'Creating user_history table...';
        CREATE TABLE public.user_history (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX idx_user_history_user_id ON public.user_history(user_id);
        CREATE INDEX idx_user_history_timestamp ON public.user_history(timestamp DESC);
        
        ALTER TABLE public.user_history ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY "Users can view own history" ON public.user_history
            FOR SELECT USING (auth.uid() = user_id);
        CREATE POLICY "Users can insert own history" ON public.user_history
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;
    
    -- Check if generated_documents table exists
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'generated_documents') THEN
        RAISE NOTICE 'Creating generated_documents table...';
        CREATE TABLE public.generated_documents (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
            document_type TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            title TEXT,
            content TEXT NOT NULL,
            data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX idx_generated_documents_user_id ON public.generated_documents(user_id);
        CREATE INDEX idx_generated_documents_created_at ON public.generated_documents(created_at DESC);
        
        ALTER TABLE public.generated_documents ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY "Users can view own documents" ON public.generated_documents
            FOR SELECT USING (auth.uid() = user_id);
        CREATE POLICY "Users can insert own documents" ON public.generated_documents
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        CREATE POLICY "Users can update own documents" ON public.generated_documents
            FOR UPDATE USING (auth.uid() = user_id);
        CREATE POLICY "Users can delete own documents" ON public.generated_documents
            FOR DELETE USING (auth.uid() = user_id);
            
        CREATE TRIGGER update_generated_documents_updated_at BEFORE UPDATE ON public.generated_documents
            FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
    END IF;
    
    -- Check if document_templates table exists
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'document_templates') THEN
        RAISE NOTICE 'Creating document_templates table...';
        CREATE TABLE public.document_templates (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
            name TEXT NOT NULL,
            document_type TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            template_content TEXT NOT NULL,
            is_public BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX idx_document_templates_user_id ON public.document_templates(user_id);
        
        ALTER TABLE public.document_templates ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY "Users can view own templates" ON public.document_templates
            FOR SELECT USING (auth.uid() = user_id OR is_public = true);
        CREATE POLICY "Users can insert own templates" ON public.document_templates
            FOR INSERT WITH CHECK (auth.uid() = user_id);
        CREATE POLICY "Users can update own templates" ON public.document_templates
            FOR UPDATE USING (auth.uid() = user_id);
        CREATE POLICY "Users can delete own templates" ON public.document_templates
            FOR DELETE USING (auth.uid() = user_id);
            
        CREATE TRIGGER update_document_templates_updated_at BEFORE UPDATE ON public.document_templates
            FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
    END IF;
    
    RAISE NOTICE 'Migration completed successfully!';
END
$$;