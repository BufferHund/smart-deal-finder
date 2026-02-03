'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
    id: number;
    email: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
    register: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = '/api';

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Load token from localStorage on mount
    useEffect(() => {
        const savedToken = localStorage.getItem('auth_token');
        if (savedToken) {
            setToken(savedToken);
            // Verify token by fetching user info
            fetchUser(savedToken);
        } else {
            setIsLoading(false);
        }
    }, []);

    const fetchUser = async (authToken: string) => {
        try {
            const res = await fetch(`${API_BASE}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            if (res.ok) {
                const userData = await res.json();
                setUser(userData);
                setToken(authToken);
            } else {
                // Token invalid, clear it
                localStorage.removeItem('auth_token');
                setToken(null);
                setUser(null);
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
            localStorage.removeItem('auth_token');
            setToken(null);
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (email: string, password: string) => {
        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (!res.ok) {
                return { success: false, error: data.detail || 'Login failed' };
            }

            localStorage.setItem('auth_token', data.token);
            setToken(data.token);
            setUser(data.user);

            return { success: true };
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    };

    const register = async (email: string, password: string) => {
        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (!res.ok) {
                return { success: false, error: data.detail || 'Registration failed' };
            }

            localStorage.setItem('auth_token', data.token);
            setToken(data.token);
            setUser(data.user);

            return { success: true };
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

// Helper to get auth header for API calls
export function getAuthHeader(): HeadersInit {
    const token = localStorage.getItem('auth_token');
    if (token) {
        return { 'Authorization': `Bearer ${token}` };
    }
    return {};
}
