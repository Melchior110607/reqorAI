'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();
  
  // Pages publiques (pas besoin d'auth)
  const publicPages = ['/login', '/register', '/oauth-success', '/email-callback'];
  const isPublicPage = publicPages.includes(pathname);

  useEffect(() => {
    // Rediriger vers login si non authentifié et pas sur page publique
    if (!loading && !isAuthenticated && !isPublicPage) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, isPublicPage, router]);

  // Pages publiques sans layout
  if (isPublicPage) {
    return <>{children}</>;
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Non authentifié (en cours de redirection)
  if (!isAuthenticated) {
    return null;
  }

  // Pages authentifiées avec layout
  return (
    <>
      <Navbar />
      <div className="flex pt-16">
        <Sidebar />
        <main className="flex-1 ml-64 p-8 bg-gray-50 min-h-screen">
          {children}
        </main>
      </div>
    </>
  );
}

