'use client';

import { Home, Wallet, ShoppingCart, MapPinned, User } from 'lucide-react';
import { motion } from 'framer-motion';

interface BottomNavProps {
    activeTab: string;
    onChange: (tab: string) => void;
}

export default function BottomNav({ activeTab, onChange }: BottomNavProps) {
    const tabs = [
        { id: 'deals', icon: Home, label: 'Deals' },
        { id: 'wallet', icon: Wallet, label: 'Cards' },
        { id: 'list', icon: ShoppingCart, label: 'List' },
        { id: 'map', icon: MapPinned, label: 'Map' },
        { id: 'me', icon: User, label: 'Me' },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-white/70 dark:bg-black/20 backdrop-blur-2xl border-t border-white/20 dark:border-white/10 px-6 py-4 pb-8 z-50 flex justify-between items-center rounded-t-3xl shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.1)]">
            {tabs.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                    <button
                        key={tab.id}
                        onClick={() => onChange(tab.id)}
                        className={`relative flex flex-col items-center gap-1 transition-colors duration-300 ${isActive ? 'text-black dark:text-white' : 'text-black/40 dark:text-white/40 hover:text-black/60 dark:hover:text-white/60'}`}
                    >
                        {isActive && (
                            <motion.div
                                layoutId="nav-pill"
                                className="absolute -inset-4 bg-black/5 dark:bg-white/10 rounded-2xl -z-10"
                                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                            />
                        )}
                        <tab.icon className={`w-6 h-6 ${isActive ? 'stroke-[2.5px]' : 'stroke-2'}`} />
                        <span className="text-[10px] font-medium">{tab.label}</span>
                    </button>
                );
            })}
        </div>
    );
}
