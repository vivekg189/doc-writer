// This script assumes the Supabase client library is loaded globally before it, e.g.:
// <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

(function() {
    // Ensure window.supabase and window.supabase.createClient are available
    if (typeof window.supabase === 'undefined' || typeof window.supabase.createClient === 'undefined') {
        console.error("Supabase client library not found in global scope. Ensure it\'s loaded before auth.js.");
        return;
    }

    const supabaseUrl = window.SUPABASE_URL;
    const supabaseAnonKey = window.SUPABASE_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
        console.error("Supabase URL or Anon Key not found in window object. Make sure they are passed from the Flask backend.");
        return;
    }

    const supabase = window.supabase.createClient(supabaseUrl, supabaseAnonKey);

    // Authentication related functions
    class Auth {
        static async isLoggedIn() {
            const { data: { session } } = await supabase.auth.getSession();
            return session !== null;
        }

        static async getToken() {
            const { data: { session } } = await supabase.auth.getSession();
            return session ? session.access_token : null;
        }

        static async login(email, password) {
            try {
                const { data, error } = await supabase.auth.signInWithPassword({
                    email: email,
                    password: password,
                });

                if (error) {
                    throw error;
                }
                return data;
            } catch (error) {
                throw error;
            }
        }

        static async signup(email, password) {
            try {
                const { data, error } = await supabase.auth.signUp({
                    email: email,
                    password: password,
                });

                if (error) {
                    throw error;
                }
                return data;
            } catch (error) {
                throw error;
            }
        }

        static async logout() {
            const { error } = await supabase.auth.signOut();
            if (error) {
                throw error;
            }
            window.location.href = '/';
        }

        static async makeAuthenticatedRequest(url, options = {}) {
            const { data: { session }, error: sessionError } = await supabase.auth.getSession();
            if (sessionError) {
                throw sessionError;
            }

            const token = session ? session.access_token : null;
            if (!token) {
                window.location.href = '/login.html';
                throw new Error('No authentication token found or session expired');
            }

            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            };

            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                window.location.href = '/login.html';
                throw new Error('Session expired. Please log in again.');
            }

            return response;
        }
    }

    // Expose the Auth class globally
    window.Auth = Auth;

})(); // Immediately-invoked function expression (IIFE)
