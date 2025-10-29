-- Enable RLS on tables
ALTER TABLE user_history ENABLE ROW LEVEL SECURITY;

-- User history table policies
-- Allow authenticated users to insert their own history
CREATE POLICY "Users can insert own history" ON user_history
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Allow authenticated users to read their own history
CREATE POLICY "Users can view own history" ON user_history
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Allow service role to insert/read all history (for server-side operations)
CREATE POLICY "Service role can manage history" ON user_history
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
