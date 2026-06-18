'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Skip guard on public pages
    if (pathname === '/login' || pathname === '/auth/callback') {
      setReady(true);
      return;
    }

    if (!isAuthenticated) {
      router.replace('/login');
    } else {
      setReady(true);
    }
  }, [isAuthenticated, pathname, router]);

  // On public pages, always render
  if (pathname === '/login' || pathname === '/auth/callback') {
    return <>{children}</>;
  }

  // While checking auth or redirecting, show nothing (avoid flash of protected content)
  if (!ready) {
    return null;
  }

  return <>{children}</>;
}