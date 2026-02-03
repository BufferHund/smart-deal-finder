'use client';

import { useState } from 'react';
import Navbar from '../../components/Navbar';
import BottomNav from '../../components/BottomNav';
import DealsView from '../../components/views/DealsView';
import WalletView from '../../components/views/WalletView';
import SmartListView from '../../components/views/SmartListView';
import MapView from '../../components/views/MapView';
import ProfileView from '../../components/views/ProfileView';
import { motion, AnimatePresence } from 'framer-motion';

export default function ShopperPage() {
    const [activeTab, setActiveTab] = useState("deals");

    const renderView = () => {
        switch (activeTab) {
            case "deals": return <DealsView />;
            case "wallet": return <WalletView />;
            case "list": return <SmartListView />;
            case "map": return <MapView />;
            case "me": return <ProfileView />;
            default: return <DealsView />;
        }
    };

    return (
        <div className="min-h-screen bg-[#F5F5F7] dark:bg-[#0d1117] relative transition-colors duration-300">
            {/* Background Pattern & Orbs */}
            <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: "url('/bg-pattern.svg')" }} />

            {/* Ambient Gradient for Light Mode */}
            <div className="fixed top-0 left-0 w-full h-[500px] bg-gradient-to-b from-purple-500/5 to-transparent pointer-events-none dark:hidden" />
            <div className="fixed -top-20 -right-20 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl pointer-events-none dark:hidden" />
            <div className="fixed top-40 -left-20 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl pointer-events-none dark:hidden" />

            {/* Desktop Navbar (Hidden on mobile if we want pure app feel, but good to keep for now) */}
            <div className="hidden md:block">
                <Navbar />
            </div>

            {/* Main Content Area */}
            <div className="relative z-10 h-full">
                {/* Mobile Header Removed as requested */}

                <main className="md:pt-4">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.15 }}
                        >
                            {renderView()}
                        </motion.div>
                    </AnimatePresence>
                </main>
            </div>

            {/* Bottom Navigation */}
            <BottomNav activeTab={activeTab} onChange={setActiveTab} />
        </div>
    );
}
