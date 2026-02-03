'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

// Pages that don't require authentication
const PUBLIC_PATHS = ['/login', '/'];

export function AuthGuard({ children }: { children: React.ReactNode }) {
    const { user, isLoading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        if (!isLoading && !user && !PUBLIC_PATHS.includes(pathname)) {
            router.push('/login');
        }
    }, [user, isLoading, pathname, router]);

    // Show loading state
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
            </div>
        );
    }

    // Not logged in and not on public page
    if (!user && !PUBLIC_PATHS.includes(pathname)) {
        return null; // Will redirect in useEffect
    }

    return <>{children}</>;
}
