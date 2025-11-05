# Database Setup Guide

This guide explains how to set up the Supabase database for the Legal Document Writer application.

## Prerequisites

1. A Supabase account and project
2. Access to the Supabase SQL Editor
3. Your Supabase URL and Service Role Key

## Setup Steps

### 1. Run the Main Schema

1. Open your Supabase dashboard
2. Go to the SQL Editor
3. Copy and paste the contents of `supabase_schema.sql`
4. Click "Run" to execute the script

This will create:
- `users` table (extends Supabase auth.users)
- `user_history` table (stores user activity)
- `generated_documents` table (stores generated documents)
- `document_templates` table (stores custom templates)
- All necessary indexes and Row Level Security policies
- Triggers for automatic user profile creation

### 2. Add Sample Data (Optional)

1. In the SQL Editor, copy and paste the contents of `supabase_sample_data.sql`
2. Click "Run" to execute the script

This will add some basic document templates that users can use.

### 3. Migration for Existing Installations

If you already have a running application with existing data:

1. In the SQL Editor, copy and paste the contents of `supabase_migration.sql`
2. Click "Run" to execute the script

This will safely add new tables without affecting existing data.

## Environment Variables

Make sure your `.env` file has the correct Supabase credentials:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
```

## Verification

After running the scripts, you should see the following tables in your Supabase dashboard:

1. **users** - User profiles
2. **user_history** - Activity tracking
3. **generated_documents** - Saved documents
4. **document_templates** - Custom templates

## Row Level Security (RLS)

All tables have RLS enabled with the following policies:

- Users can only access their own data
- Public templates are visible to all users
- Service role key bypasses RLS for server operations

## Troubleshooting

### Common Issues

1. **"relation does not exist" error**
   - Make sure you ran `supabase_schema.sql` first
   - Check that the tables were created in the `public` schema

2. **Permission denied errors**
   - Verify your service role key is correct
   - Check that RLS policies are properly configured

3. **History not saving**
   - Check the browser console for errors
   - Verify the user is logged in (session contains user_id)
   - Check Supabase logs for database errors

### Debug Mode

The application includes debug logging. Check your server console for messages like:
- "Supabase client initialized successfully"
- "Inserting history: ..."
- "History insert response: ..."

## Database Schema

### users
- `id` (UUID, Primary Key, references auth.users)
- `email` (TEXT, Unique)
- `username` (TEXT)
- `full_name` (TEXT)
- `avatar_url` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### user_history
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to users)
- `action` (TEXT) - Type of action performed
- `details` (TEXT) - Additional details about the action
- `timestamp` (TIMESTAMP)
- `created_at` (TIMESTAMP)

### generated_documents
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to users)
- `document_type` (TEXT) - Type of document
- `language` (TEXT) - Document language
- `title` (TEXT) - Document title
- `content` (TEXT) - Generated document content
- `data` (JSONB) - Form data used to generate the document
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### document_templates
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to users)
- `name` (TEXT) - Template name
- `document_type` (TEXT) - Type of document
- `language` (TEXT) - Template language
- `template_content` (TEXT) - Jinja2 template content
- `is_public` (BOOLEAN) - Whether template is public
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## Support

If you encounter issues:
1. Check the Supabase dashboard logs
2. Review the server console output
3. Verify your environment variables
4. Ensure all SQL scripts ran successfully