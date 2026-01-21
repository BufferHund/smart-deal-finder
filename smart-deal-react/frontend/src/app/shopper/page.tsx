'use client';

import Navbar from '../../components/Navbar';
import DealCard from '../../components/DealCard';
import ChatInterface from '../../components/ChatInterface';
import { useState, useEffect } from 'react';
import { Button, useDisclosure, Input, Card, CardBody } from "@heroui/react";
import { getActiveDeals, getShoppingList, addToShoppingList, removeFromShoppingList } from '../../lib/api';
import { motion, AnimatePresence } from 'framer-motion';

export default function ShopperPage() {
    const [deals, setDeals] = useState<any[]>([]);
    const [shoppingList, setShoppingList] = useState<string[]>([]);
    const { isOpen: isChatOpen, onOpen: onChatOpen, onOpenChange: onChatOpenChange } = useDisclosure();
    const [isListOpen, setIsListOpen] = useState(false);
    const [newItem, setNewItem] = useState("");
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setIsLoading(true);
        try {
            const dealData = await getActiveDeals();
            if (dealData && dealData.deals) setDeals(dealData.deals);

            const listData = await getShoppingList();
            if (Array.isArray(listData)) setShoppingList(listData);
        } catch (e) {
            console.error("Failed to load shopper data", e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAddToList = async (item: string) => {
        try {
            const res = await addToShoppingList({ item });
            setShoppingList(res.list);
            setIsListOpen(true);
        } catch (e) {
            console.error("Add failed", e);
        }
    };

    const handleRemoveFromList = async (item: string) => {
        try {
            const res = await removeFromShoppingList({ item });
            setShoppingList(res.list);
        } catch (e) {
            console.error("Remove failed", e);
        }
    };

    const handleManualAdd = () => {
        if (newItem.trim()) {
            handleAddToList(newItem);
            setNewItem("");
        }
    }

    return (
        <div className="min-h-screen pt-24 pb-20 px-4 relative">
            {/* Background Pattern Overlay */}
            <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: "url('/bg-pattern.svg')" }} />

            <div className="relative z-10">
                <Navbar />

                <div className="container mx-auto max-w-7xl">
                    {/* Header Section */}
                    <div className="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
                        <div>
                            <h1 className="text-4xl font-black text-white mb-2 tracking-tight">
                                Today's <span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-purple-500">Best Buys</span>
                            </h1>
                            <p className="text-white/60">Curated deals just for you.</p>
                        </div>

                        <Button
                            size="lg"
                            className="bg-white/10 backdrop-blur-md border border-white/20 text-white font-bold shadow-xl hover:bg-white/20"
                            onPress={() => setIsListOpen(!isListOpen)}
                            endContent={<span className="bg-pink-500 text-white text-xs px-2 py-0.5 rounded-full ml-2">{shoppingList.length}</span>}
                        >
                            Shopping List
                        </Button>
                    </div>

                    {/* Deals Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                        {isLoading ? (
                            // Skeleton Loading State
                            Array.from({ length: 10 }).map((_, i) => (
                                <Card key={i} className="h-64 bg-white/5 border border-white/10" radius="lg">
                                    <div className="h-32 rounded-t-lg bg-white/10 animate-pulse" />
                                    <div className="p-4 space-y-3">
                                        <div className="w-3/4 h-3 rounded-lg bg-white/10 animate-pulse" />
                                        <div className="w-1/2 h-3 rounded-lg bg-white/10 animate-pulse" />
                                        <div className="w-full h-8 rounded-lg bg-white/10 animate-pulse mt-4" />
                                    </div>
                                </Card>
                            ))
                        ) : deals.length > 0 ? (
                            deals.map((deal, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                >
                                    <DealCard deal={deal} onAdd={handleAddToList} />
                                </motion.div>
                            ))
                        ) : (
                            <div className="col-span-full py-20 text-center">
                                <div className="text-6xl mb-4">👻</div>
                                <h3 className="text-2xl font-bold text-white/50">No deals found here.</h3>
                                <p className="text-white/30">Check back later or upload a flyer in Admin.</p>
                            </div>
                        )}
                    </div>

                    {/* Empty State Check (Only if loaded and empty) */}
                    {deals.length === 0 && deals !== null && (
                        // Note: We need a 'loading' state tracker to differentiate between 'loading' and 'empty'.
                        // For now, simpler skeleton is better than flash of empty content.
                        // Ideally, we add isLoading state to loadData.
                        null
                    )}

                    {/* Floating Chat Button */}
                    <motion.div
                        className="fixed bottom-8 right-8 z-50"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        <Button
                            isIconOnly
                            className="w-16 h-16 rounded-full bg-gradient-to-tr from-pink-500 to-indigo-600 shadow-lg shadow-indigo-500/40 border border-white/20"
                            onPress={onChatOpen}
                        >
                            <span className="text-3xl">👨‍🍳</span>
                        </Button>
                    </motion.div>

                    <ChatInterface isOpen={isChatOpen} onOpenChange={onChatOpenChange} />

                    {/* Shopping List Drawer (Custom Glass Overlay) */}
                    <AnimatePresence>
                        {isListOpen && (
                            <motion.div
                                initial={{ x: "100%" }}
                                animate={{ x: 0 }}
                                exit={{ x: "100%" }}
                                transition={{ type: "spring", damping: 25 }}
                                className="fixed top-0 right-0 h-full w-full sm:w-96 bg-[#161b22]/90 backdrop-blur-2xl border-l border-white/10 shadow-2xl z-[60] pt-24 px-6 pb-6"
                            >
                                <div className="flex flex-col h-full">
                                    <div className="flex justify-between items-center mb-6">
                                        <h2 className="text-2xl font-bold text-white">Your List 📝</h2>
                                        <Button size="sm" isIconOnly variant="light" onPress={() => setIsListOpen(false)} className="text-white/50 hover:text-white">✕</Button>
                                    </div>

                                    <div className="flex gap-2 mb-6">
                                        <Input
                                            placeholder="Add custom item..."
                                            value={newItem}
                                            onChange={(e) => setNewItem(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleManualAdd()}
                                            classNames={{
                                                inputWrapper: "bg-white/5 border border-white/10"
                                            }}
                                        />
                                        <Button isIconOnly color="primary" onPress={handleManualAdd}>+</Button>
                                    </div>

                                    <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                                        {shoppingList.length === 0 ? (
                                            <div className="text-center mt-10 text-white/20">
                                                <div className="text-4xl mb-2">🛒</div>
                                                <p>List is empty</p>
                                            </div>
                                        ) : (
                                            <ul className="space-y-3">
                                                {shoppingList.map((item, i) => (
                                                    <motion.li
                                                        key={i}
                                                        initial={{ opacity: 0, x: -20 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/5 hover:border-white/20 transition-colors group"
                                                    >
                                                        <span className="text-white/90 font-medium">{item}</span>
                                                        <Button
                                                            size="sm"
                                                            color="danger"
                                                            variant="light"
                                                            isIconOnly
                                                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                                                            onPress={() => handleRemoveFromList(item)}
                                                        >
                                                            ✕
                                                        </Button>
                                                    </motion.li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>

                                    <div className="mt-6">
                                        <Button fullWidth className="bg-gradient-to-r from-emerald-500 to-green-600 text-white font-bold shadow-lg">
                                            Export to WhatsApp
                                        </Button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
