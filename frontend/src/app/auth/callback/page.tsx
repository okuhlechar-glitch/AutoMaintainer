'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const error = params.get('error');

    if (error) {
      // Redirect to login with error message
      router.replace(`/login?error=${encodeURIComponent(error)}`);
      return;
    }

    if (token) {
      localStorage.setItem('automaintainer_token', token);
      router.replace('/');
    } else {
      router.replace('/login?error=No token received from GitHub');
    }
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-am-dark">
      <div className="flex items-center gap-3 text-am-muted">
        <span className="w-5 h-5 border-2 border-am-accent/30 border-t-am-accent rounded-full animate-spin" />
        Completing sign in...
      </div>
    </div>
  );
}
