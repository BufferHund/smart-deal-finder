'use client'

import { HeroUIProvider } from '@heroui/react'
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { AuthProvider } from "@/contexts/AuthContext";
import { AuthGuard } from "@/components/AuthGuard";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <HeroUIProvider>
            <NextThemesProvider attribute="class" defaultTheme="light">
                <AuthProvider>
                    <AuthGuard>
                        {children}
                    </AuthGuard>
                </AuthProvider>
            </NextThemesProvider>
        </HeroUIProvider>
    )
}
