'use client';

import { Card, CardBody, Input, Button, Tabs, Tab, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure, Select, SelectItem } from "@heroui/react";
import { Search, Sparkles, Trash2, TrendingDown, Store, Mic, MicOff, Camera, Settings, MapPin } from "lucide-react";
import { useState, useEffect, useRef } from 'react';
import { getShoppingList, addToShoppingList, removeFromShoppingList, chatWithChef, optimizeList, scanFridge } from '../../lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import RouteAgentModal from '../RouteAgentModal';

export default function SmartListView() {
    const [items, setItems] = useState<string[]>([]);
    const [newItem, setNewItem] = useState("");
    const [activeTab, setActiveTab] = useState("list");

    // Chef State
    const [chefMessage, setChefMessage] = useState("");
    const [chefResponse, setChefResponse] = useState("");
    const [isChefTyping, setIsChefTyping] = useState(false);

    const fridgeInputRef = useRef<HTMLInputElement>(null);

    // Chef Settings
    const [budget, setBudget] = useState("");
    const [diet, setDiet] = useState("None");
    const [showSettings, setShowSettings] = useState(false);

    // Optimization State
    const [optimizationResult, setOptimizationResult] = useState<any[] | null>(null);
    const { isOpen, onOpen, onOpenChange } = useDisclosure();
    const [isOptimizing, setIsOptimizing] = useState(false);

    // Voice State
    const [isListening, setIsListening] = useState(false);

    // Route Planning State
    const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
    const { isOpen: isRouteOpen, onOpen: onRouteOpen, onClose: onRouteClose } = useDisclosure();

    // Get user location on mount
    useEffect(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => setUserLocation([pos.coords.latitude, pos.coords.longitude]),
                () => setUserLocation([52.52, 13.405]) // Default Berlin
            );
        }
    }, []);

    useEffect(() => {
        loadList();
    }, []);

    const loadList = async () => {
        try {
            const data = await getShoppingList();
            if (Array.isArray(data)) setItems(data);
        } catch (e) {
            console.error(e);
        }
    };

    const handleAdd = async (value?: string) => {
        const itemToAdd = value || newItem;
        if (!itemToAdd.trim()) return;
        try {
            const res = await addToShoppingList({ item: itemToAdd });
            setItems(res.list);
            if (!value) setNewItem("");
        } catch (e) {
            console.error(e);
        }
    };

    const handleRemove = async (item: string) => {
        try {
            const res = await removeFromShoppingList({ item });
            setItems(res.list);
        } catch (e) {
            console.error(e);
        }
    };

    const handleOptimize = async () => {
        if (items.length === 0) return;
        setIsOptimizing(true);
        try {
            const res = await optimizeList(items);
            if (res.optimization) {
                setOptimizationResult(res.optimization);
                onOpen();
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsOptimizing(false);
        }
    };

    const handleAskChef = async () => {
        if (!chefMessage.trim()) return;
        setIsChefTyping(true);
        try {
            const prompt = `Based on my shopping list (${items.join(', ')}), ${chefMessage}`;
            const context = { budget, diet };
            const res = await chatWithChef(prompt, context);
            setChefResponse(res.response);
        } catch (e) {
            console.error(e);
        } finally {
            setIsChefTyping(false);
        }
    };

    const handleFridgeScan = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setIsChefTyping(true);
            setChefResponse("Analyzing your fridge... 📸");
            try {
                const data = await scanFridge(file);
                if (data.message) {
                    setChefResponse(`📸 **I see:** ${data.ingredients.join(", ")}\n\n🥘 **Recipe Idea:** ${data.recipe_name}\n\n💡 ${data.message}`);
                } else if (data.response) {
                    setChefResponse(data.response);
                }
            } catch (err) {
                setChefResponse("I couldn't identify the food. Try again?");
            } finally {
                setIsChefTyping(false);
            }
        }
    };

    const toggleVoice = () => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Your browser does not support voice search.");
            return;
        }

        if (isListening) {
            setIsListening(false);
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => setIsListening(true);
        recognition.onend = () => setIsListening(false);

        recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript;
            setNewItem(transcript);
        };

        recognition.start();
    };

    return (
        <div className="p-4 space-y-6 pb-24 h-full flex flex-col">
            <header className="mb-2">
                <h1 className="text-3xl font-black text-black dark:text-white">Smart List</h1>
                <p className="text-black/50 dark:text-white/50 text-sm">Plan & Cook</p>
            </header>

            <Tabs
                selectedKey={activeTab}
                onSelectionChange={(key) => setActiveTab(key as string)}
                variant="bordered"
                radius="full"
                classNames={{
                    tabList: "bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 w-full",
                    cursor: "bg-pink-500",
                    tabContent: "text-black/80 dark:text-white/80 group-data-[selected=true]:text-white font-bold"
                }}
            >
                <Tab key="list" title="Shopping List" />
                <Tab key="chef" title="AI Chef Ideas" />
            </Tabs>

            <AnimatePresence mode="wait">
                {activeTab === 'list' ? (
                    <motion.div
                        key="list-view"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className="flex-1 flex flex-col"
                    >
                        {/* Input Area */}
                        <div className="flex gap-2 mb-4">
                            <Input
                                placeholder="Add item (e.g. Milk)"
                                value={newItem}
                                onChange={(e) => setNewItem(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                                classNames={{
                                    inputWrapper: "bg-white dark:bg-white/10 border-black/20 dark:border-white/20 text-black dark:text-white shadow-sm dark:shadow-none"
                                }}
                                startContent={<Search size={18} className="text-black/50 dark:text-white/50" />}
                            />
                            <Button isIconOnly className={isListening ? "bg-red-500 text-white animate-pulse" : "bg-black/5 dark:bg-white/10 text-black dark:text-white"} onPress={toggleVoice}>
                                {isListening ? <MicOff size={20} /> : <Mic size={20} />}
                            </Button>
                            <Button className="font-bold bg-white text-black" onPress={() => handleAdd()}>
                                Add
                            </Button>
                        </div>

                        {/* List Items */}
                        <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                            {items.length === 0 ? (
                                <div className="text-center py-10 text-black/30 dark:text-white/30">
                                    <p>Your list is empty.</p>
                                </div>
                            ) : (
                                items.map((item, i) => (
                                    <div key={i} className="flex items-center justify-between p-3 bg-white dark:bg-white/5 rounded-xl border border-black/5 dark:border-white/5 shadow-sm dark:shadow-none">
                                        <div className="flex items-center gap-3">
                                            <div className="w-5 h-5 rounded-md border-2 border-black/20 dark:border-white/20" />
                                            <span className="text-black/90 dark:text-white/90">{item}</span>
                                        </div>
                                        <Button isIconOnly size="sm" variant="light" color="danger" onPress={() => handleRemove(item)}>
                                            <Trash2 size={16} />
                                        </Button>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Optimize Banners */}
                        {items.length > 0 && (
                            <div className="mt-4 space-y-2">
                                <Button
                                    fullWidth
                                    className="bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold shadow-lg"
                                    startContent={<MapPin size={20} />}
                                    onPress={onRouteOpen}
                                >
                                    🧭 Plan Smart Route
                                </Button>
                                <Button
                                    fullWidth
                                    className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-bold shadow-lg"
                                    startContent={<TrendingDown size={20} />}
                                    onPress={handleOptimize}
                                    isLoading={isOptimizing}
                                >
                                    Find Cheapest Store
                                </Button>
                            </div>
                        )}

                        {/* Optimization Result Modal */}
                        <Modal isOpen={isOpen} onOpenChange={onOpenChange} backdrop="blur" scrollBehavior="inside">
                            <ModalContent className="bg-white dark:bg-[#1c1c1e] text-black dark:text-white border border-black/10 dark:border-white/10">
                                {(onClose) => (
                                    <>
                                        <ModalHeader className="flex flex-col gap-1">
                                            <span>Best Deals Found</span>
                                            <span>Best Deals Found</span>
                                            <span className="text-xs text-black/50 dark:text-white/50 font-normal">Based on your list</span>
                                        </ModalHeader>
                                        <ModalBody>
                                            {optimizationResult?.length === 0 ? (
                                                <div className="text-center py-4">
                                                    <p className="text-white/60">No deals found for your items this week.</p>
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    {optimizationResult?.map((storeData, idx) => (
                                                        <div key={idx} className="bg-black/5 dark:bg-white/5 p-4 rounded-xl border border-black/10 dark:border-white/10">
                                                            <div className="flex justify-between items-center mb-2">
                                                                <h3 className="text-lg font-bold flex items-center gap-2 text-black dark:text-white">
                                                                    <Store size={18} /> {storeData.store}
                                                                </h3>
                                                                <div className="text-right">
                                                                    <div className="text-xl font-black text-green-600 dark:text-green-400">{storeData.total_price} €</div>
                                                                    <div className="text-xs text-black/50 dark:text-white/50">{storeData.match_count} items matched</div>
                                                                </div>
                                                            </div>

                                                            <div className="space-y-1">
                                                                {storeData.matches.map((match: any, matchIdx: number) => (
                                                                    <div key={matchIdx} className="flex justify-between text-sm py-1 border-t border-black/5 dark:border-white/5">
                                                                        <span className="text-black/80 dark:text-white/80">{match.product}</span>
                                                                        <span className="font-mono text-black dark:text-white">{match.price} €</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </ModalBody>
                                        <ModalFooter>
                                            <Button color="primary" onPress={onClose}>
                                                Done
                                            </Button>
                                        </ModalFooter>
                                    </>
                                )}
                            </ModalContent>
                        </Modal>
                    </motion.div>
                ) : (
                    <motion.div
                        key="chef-view"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col"
                    >
                        <Card className="bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/50 dark:to-purple-900/50 border-none mb-4">
                            <CardBody className="flex flex-row items-center gap-4">
                                <div className="p-3 bg-white rounded-full shadow-sm dark:bg-white/10 dark:shadow-none">
                                    <Sparkles size={24} className="text-yellow-500 dark:text-yellow-300" />
                                </div>
                                <p className="text-black/80 dark:text-white/80 text-sm">
                                    I can suggest <b>recipes</b> based on your shopping list!
                                </p>
                            </CardBody>
                        </Card>

                        <div className="flex-1 overflow-y-auto bg-black/5 dark:bg-white/5 rounded-2xl p-4 mb-4 border border-black/10 dark:border-white/10">
                            {chefResponse ? (
                                <div>
                                    <p className="text-pink-600 dark:text-pink-400 font-bold mb-2">Chef says:</p>
                                    <p className="text-black/80 dark:text-white/80 whitespace-pre-wrap">{chefResponse}</p>
                                </div>
                            ) : (
                                <p className="text-black/30 dark:text-white/30 text-center mt-10">Ask me anything about your groceries...</p>
                            )}
                            {isChefTyping && <p className="text-black/50 dark:text-white/50 animate-pulse mt-2">Thinking...</p>}
                        </div>

                        <div className="flex gap-2">
                            <input
                                type="file"
                                ref={fridgeInputRef}
                                className="hidden"
                                accept="image/*"
                                onChange={handleFridgeScan}
                            />
                            <Button isIconOnly className="bg-black/5 dark:bg-white/10 text-black dark:text-white" onPress={() => fridgeInputRef.current?.click()}>
                                <Camera size={20} />
                            </Button>
                            <Input
                                placeholder="What can I cook with this?"
                                value={chefMessage}
                                onChange={(e) => setChefMessage(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAskChef()}
                                classNames={{
                                    inputWrapper: "bg-black/5 dark:bg-white/10 border-black/20 dark:border-white/20 text-black dark:text-white"
                                }}
                            />
                            <Button isIconOnly color="secondary" onPress={handleAskChef} isLoading={isChefTyping}>
                                ➤
                            </Button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Route Agent Modal */}
            <RouteAgentModal
                isOpen={isRouteOpen}
                onClose={onRouteClose}
                items={items}
                userLocation={userLocation}
                onRouteConfirmed={(stores) => {
                    console.log('Route confirmed:', stores);
                }}
            />
        </div>
    );

}
