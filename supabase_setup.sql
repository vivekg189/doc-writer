-- Complete Supabase Setup for Legal Document Writer
-- Run this entire script in Supabase SQL Editor to set up the database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS public.generated_documents CASCADE;
DROP TABLE IF EXISTS public.user_history CASCADE;
DROP TABLE IF EXISTS public.user_profiles CASCADE;

-- Create user_profiles table (no foreign key constraint)
CREATE TABLE public.user_profiles (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    language_preference TEXT NOT NULL DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user_history table (no foreign key constraint)
CREATE TABLE public.user_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create generated_documents table (no foreign key constraint)
CREATE TABLE public.generated_documents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    document_type TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    title TEXT,
    content TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX idx_user_profiles_language_preference ON public.user_profiles(language_preference);
CREATE INDEX idx_user_history_user_id ON public.user_history(user_id);
CREATE INDEX idx_user_history_timestamp ON public.user_history(timestamp);
CREATE INDEX idx_generated_documents_user_id ON public.generated_documents(user_id);
CREATE INDEX idx_generated_documents_created_at ON public.generated_documents(created_at);

-- Disable Row Level Security for easier development
ALTER TABLE public.user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_documents DISABLE ROW LEVEL SECURITY;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_generated_documents_updated_at BEFORE UPDATE ON public.generated_documents
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Setup complete message
SELECT 'Supabase setup completed successfully! You can now use the Legal Document Writer.' as message;