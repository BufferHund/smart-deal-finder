'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card, CardBody, CardHeader, Tabs, Tab } from '@heroui/react';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { Mail, Lock, LogIn, UserPlus, Sparkles } from 'lucide-react';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [mode, setMode] = useState<'login' | 'register'>('login');

    const { login, register } = useAuth();
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const result = mode === 'login'
                ? await login(email, password)
                : await register(email, password);

            if (result.success) {
                router.push('/shopper');
            } else {
                setError(result.error || 'Authentication failed');
            }
        } catch (err) {
            setError('An error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-indigo-900 p-4">
            {/* Background decoration */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-300 dark:bg-purple-900/30 rounded-full blur-3xl opacity-50" />
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-300 dark:bg-indigo-900/30 rounded-full blur-3xl opacity-50" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md relative z-10"
            >
                <Card className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl shadow-2xl border border-gray-200 dark:border-gray-700">
                    <CardHeader className="flex flex-col items-center gap-3 pt-8 pb-4">
                        <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: 'spring', delay: 0.2 }}
                            className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg"
                        >
                            <Sparkles className="w-8 h-8 text-white" />
                        </motion.div>
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">SmartDeal</h1>
                        <p className="text-gray-500 dark:text-gray-400 text-sm">Your AI Shopping Assistant</p>
                    </CardHeader>

                    <CardBody className="px-6 pb-8">
                        <Tabs
                            selectedKey={mode}
                            onSelectionChange={(key) => {
                                setMode(key as 'login' | 'register');
                                setError('');
                            }}
                            className="mb-6"
                            fullWidth
                            size="lg"
                        >
                            <Tab key="login" title={<span className="flex items-center gap-2"><LogIn size={16} /> Login</span>} />
                            <Tab key="register" title={<span className="flex items-center gap-2"><UserPlus size={16} /> Register</span>} />
                        </Tabs>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <Input
                                type="email"
                                label="Email"
                                placeholder="your@email.com"
                                value={email}
                                onValueChange={setEmail}
                                startContent={<Mail className="text-gray-400" size={18} />}
                                isRequired
                                variant="bordered"
                                classNames={{
                                    input: "text-gray-900 dark:text-white",
                                    label: "text-gray-600 dark:text-gray-400"
                                }}
                            />

                            <Input
                                type="password"
                                label="Password"
                                placeholder={mode === 'register' ? 'At least 6 characters' : 'Your password'}
                                value={password}
                                onValueChange={setPassword}
                                startContent={<Lock className="text-gray-400" size={18} />}
                                isRequired
                                variant="bordered"
                                classNames={{
                                    input: "text-gray-900 dark:text-white",
                                    label: "text-gray-600 dark:text-gray-400"
                                }}
                            />

                            {error && (
                                <motion.p
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="text-red-500 text-sm text-center bg-red-50 dark:bg-red-900/20 p-2 rounded-lg"
                                >
                                    {error}
                                </motion.p>
                            )}

                            <Button
                                type="submit"
                                color="primary"
                                size="lg"
                                fullWidth
                                isLoading={isLoading}
                                className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold shadow-lg hover:shadow-xl transition-shadow"
                            >
                                {mode === 'login' ? 'Sign In' : 'Create Account'}
                            </Button>
                        </form>

                        <p className="text-center text-xs text-gray-400 mt-6">
                            By continuing, you agree to our Terms of Service
                        </p>
                    </CardBody>
                </Card>
            </motion.div>
        </div>
    );
}
