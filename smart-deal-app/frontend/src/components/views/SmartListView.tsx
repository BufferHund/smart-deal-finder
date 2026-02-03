'use client';

import { Card, CardBody, Input, Button, Tabs, Tab, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure, Select, SelectItem } from "@heroui/react";
import { Search, Sparkles, Trash2, TrendingDown, Store, Mic, MicOff, Camera, Settings, MapPin, UtensilsCrossed, DollarSign, Snowflake, AlertTriangle, Lightbulb, Eye, ChefHat, ShoppingCart } from "lucide-react";
import { useState, useEffect, useRef } from 'react';
import { getShoppingList, addToShoppingList, removeFromShoppingList, chatWithChef, optimizeList, scanFridge } from '../../lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import RouteAgentModal from '../RouteAgentModal';

export default function SmartListView() {
    const [items, setItems] = useState<string[]>([]);
    const [newItem, setNewItem] = useState("");
    const [activeTab, setActiveTab] = useState("list");

    // Chef State
    const [chefMessage, setChefMessage] = useState("");
    // Chat History State
    const [messages, setMessages] = useState<{ role: 'user' | 'chef', content: string }[]>([]);
    const [chefRecipes, setChefRecipes] = useState<any[]>([]);
    const [isChefTyping, setIsChefTyping] = useState(false);

    // Quick Actions - 3 essentials
    const quickActions = [
        { label: "Dinner Ideas", prompt: "What can I cook for dinner?", icon: UtensilsCrossed },
        { label: "Best Deals", prompt: "Show me the best deals", icon: DollarSign },
        { label: "Use My Fridge", prompt: "Help me use what I have", icon: Snowflake }
    ];

    const fridgeInputRef = useRef<HTMLInputElement>(null);

    // Chef Settings
    const [budget, setBudget] = useState("");
    const [diet, setDiet] = useState("None");
    const [showSettings, setShowSettings] = useState(false);

    // Context Toggles - simplified
    const [useShoppingList, setUseShoppingList] = useState(true);
    const [useDeals, setUseDeals] = useState(true);

    // Optimization State
    const [optimizationResult, setOptimizationResult] = useState<any>(null);
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
            setOptimizationResult(res); // Store full response
            onOpen();
        } catch (e) {
            console.error(e);
        } finally {
            setIsOptimizing(false);
        }
    };

    const handleAskChef = async (overrideMessage?: string) => {
        const msgToSend = overrideMessage || chefMessage;

        if (!msgToSend.trim()) return;

        // 1. Add User Message to History
        const newHistory = [...messages, { role: 'user' as const, content: msgToSend }];
        setMessages(newHistory);

        setChefMessage(""); // Clear input
        setIsChefTyping(true);

        try {
            let prompt = msgToSend;

            if (useShoppingList && items.length > 0) {
                prompt = `Based on my shopping list (${items.join(', ')}), ${msgToSend}`;
            }

            const context = {
                budget,
                diet,
                include_deals: useDeals,
                include_knowledge: true // Always on
            };

            // Use newHistory which includes current message
            const historyPayload = newHistory.map(m => ({ role: m.role, content: m.content }));

            const res = await chatWithChef(prompt, context, historyPayload);

            // 3. Add Chef Response to History
            setMessages(prev => [...prev, { role: 'chef', content: res.response }]);

            if (res.recipes) setChefRecipes(res.recipes);
        } catch (e: any) {
            console.error(e);
            setMessages(prev => [...prev, { role: 'chef', content: "Error: " + (e.message || "Unknown error") }]);
        } finally {
            setIsChefTyping(false);
        }
    };

    const handleFridgeScan = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setIsChefTyping(true);
            setMessages(prev => [...prev, { role: 'chef', content: "Analyzing your fridge... 📸" }]);

            try {
                const data = await scanFridge(file);
                let responseText = "";
                if (data.message) {
                    responseText = `**I see:** ${data.ingredients.join(", ")}\n\n**Recipe Idea:** ${data.recipe_name}\n\n${data.message}`;
                } else if (data.response) {
                    responseText = data.response;
                }
                setMessages(prev => [...prev, { role: 'chef', content: responseText }]);
            } catch (err) {
                setMessages(prev => [...prev, { role: 'chef', content: "I couldn't identify the food. Try again?" }]);
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

    // Knowledge Base Upload
    const kbInputRef = useRef<HTMLInputElement>(null);
    const handleKnowledgeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            if (!file.name.endsWith('.md')) {
                alert("Please upload Markdown (.md) files only.");
                return;
            }
            try {
                // Reuse upload endpoint, basic implementation
                const formData = new FormData();
                formData.append('file', file);
                formData.append('store_name', 'KnowledgeBase');

                const res = await fetch('/api/upload', { method: 'POST', body: formData });
                if (res.ok) alert("Knowledge Base updated! Chef now knows this document.");
                else alert("Upload failed.");
            } catch (e) { console.error(e); }
        }
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
                                    className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 font-bold border border-blue-200 dark:border-blue-800"
                                    startContent={<MapPin size={18} />}
                                    onPress={onRouteOpen}
                                >
                                    Plan Smart Route
                                </Button>
                                <Button
                                    fullWidth
                                    className="bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 font-bold border border-amber-200 dark:border-amber-800"
                                    startContent={<TrendingDown size={18} />}
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
                                            <span>Store Comparison</span>
                                            <span className="text-xs text-black/50 dark:text-white/50 font-normal">
                                                {optimizationResult?.found_count || 0}/{optimizationResult?.total_items || 0} items found
                                            </span>
                                        </ModalHeader>
                                        <ModalBody>
                                            {/* Recommendation Banner */}
                                            {optimizationResult?.recommendation && (
                                                <div className="p-3 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 mb-4">
                                                    <p className="text-sm font-medium text-black dark:text-white">
                                                        {optimizationResult.recommendation}
                                                    </p>
                                                </div>
                                            )}

                                            {/* Not Found Warning */}
                                            {optimizationResult?.not_found?.length > 0 && (
                                                <div className="p-3 rounded-xl bg-orange-500/10 border border-orange-500/30 mb-4">
                                                    <p className="text-xs font-bold text-orange-600 dark:text-orange-400 mb-1 flex items-center gap-1"><AlertTriangle size={12} /> Not Found - Check These Yourself:</p>
                                                    <p className="text-sm text-black/70 dark:text-white/70">
                                                        {optimizationResult.not_found.join(', ')}
                                                    </p>
                                                </div>
                                            )}

                                            {optimizationResult?.optimization?.length === 0 ? (
                                                <div className="text-center py-4">
                                                    <p className="text-black/60 dark:text-white/60">No matches found. Try your local supermarket.</p>
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    {optimizationResult?.optimization?.map((storeData: any, idx: number) => (
                                                        <div key={idx} className="bg-black/5 dark:bg-white/5 p-4 rounded-xl border border-black/10 dark:border-white/10">
                                                            <div className="flex justify-between items-center mb-2">
                                                                <h3 className="text-lg font-bold flex items-center gap-2 text-black dark:text-white">
                                                                    <Store size={18} /> {storeData.store}
                                                                    {idx === 0 && <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full">Best</span>}
                                                                </h3>
                                                                <div className="text-right">
                                                                    <div className="text-xl font-black text-green-600 dark:text-green-400">€{storeData.total_price}</div>
                                                                    <div className="text-xs text-black/50 dark:text-white/50">{storeData.match_count} items</div>
                                                                </div>
                                                            </div>

                                                            <div className="space-y-1">
                                                                {storeData.matches.map((match: any, matchIdx: number) => (
                                                                    <div key={matchIdx} className="flex justify-between text-sm py-1 border-t border-black/5 dark:border-white/5">
                                                                        <span className="text-black/80 dark:text-white/80">{match.product}</span>
                                                                        <span className="font-mono text-black dark:text-white">€{match.price}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Category Alternatives */}
                                            {optimizationResult?.alternatives?.length > 0 && (
                                                <div className="mt-4 p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                                                    <p className="text-xs font-bold text-blue-600 dark:text-blue-400 mb-2 flex items-center gap-1"><Lightbulb size={12} /> Category Suggestions (no exact match):</p>
                                                    <div className="space-y-2">
                                                        {optimizationResult.alternatives.map((alt: any, i: number) => (
                                                            <div key={i} className="flex justify-between text-sm">
                                                                <div>
                                                                    <span className="text-black/50 dark:text-white/50 line-through mr-2">{alt.original_item}</span>
                                                                    <span className="text-black dark:text-white">→ {alt.suggestion}</span>
                                                                    <span className="text-xs text-black/40 dark:text-white/40 ml-1">@ {alt.store}</span>
                                                                </div>
                                                                <span className="font-mono text-green-600 dark:text-green-400">€{alt.price}</span>
                                                            </div>
                                                        ))}
                                                    </div>
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

                        <div className="flex-1 overflow-y-auto bg-black/5 dark:bg-white/5 rounded-2xl p-4 mb-4 border border-black/10 dark:border-white/10 flex flex-col gap-4">
                            {messages.length === 0 ? (
                                <div className="text-center mt-10 space-y-4">
                                    <p className="text-black/30 dark:text-white/30">
                                        I'm your AI Chef Agent. <br /> How can I help you save & cook today?
                                    </p>
                                    <div className="flex flex-wrap justify-center gap-2">
                                        {quickActions.map((action, idx) => (
                                            <Button
                                                key={idx}
                                                size="sm"
                                                variant="flat"
                                                className="bg-white dark:bg-white/10 shadow-sm"
                                                onPress={() => handleAskChef(action.prompt)}
                                            >
                                                {action.label}
                                            </Button>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                messages.map((msg, idx) => (
                                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-[85%] p-3 rounded-2xl ${msg.role === 'user'
                                            ? 'bg-blue-500 text-white rounded-tr-none'
                                            : 'bg-white dark:bg-white/10 border border-black/5 dark:border-white/5 rounded-tl-none'
                                            }`}>
                                            {msg.role === 'chef' && <p className="text-xs font-bold mb-1 text-pink-500">Chef Agent</p>}
                                            <div className={`text-sm ${msg.role === 'user' ? 'text-white' : 'text-black/80 dark:text-white/80'} prose dark:prose-invert max-w-none`}>
                                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}


                            {/* Render Contextual Recipe Cards at the bottom of chat if simplified, or interleaved? For now kept at bottom for simplicity */}
                            {chefRecipes.length > 0 && (
                                <div className="mt-4 space-y-3 border-t border-black/10 dark:border-white/10 pt-4">
                                    <p className="text-xs font-bold text-black/50 uppercase tracking-wider">Suggested Recipes</p>
                                    {chefRecipes.map((recipe, idx) => (
                                        <div key={idx} className="bg-white dark:bg-white/10 p-4 rounded-xl shadow-sm border border-black/5 dark:border-white/5">
                                            <div className="flex justify-between items-start mb-2">
                                                <h4 className="font-bold text-lg text-black dark:text-white">{recipe.name}</h4>
                                                <span className="text-sm font-mono bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded-md">
                                                    {recipe.estimated_cost}
                                                </span>
                                            </div>

                                            <div className="text-sm text-black/60 dark:text-white/60 mb-2">
                                                <p><strong>Ingredients:</strong> {recipe.ingredients?.join(', ')}</p>
                                            </div>

                                            <p className="text-sm text-black/80 dark:text-white/80 italic border-l-2 border-pink-500 pl-2">
                                                "{recipe.instructions}"
                                            </p>

                                            {recipe.missing_items?.length > 0 && (
                                                <Button
                                                    size="sm"
                                                    className="mt-3 w-full bg-black/5 dark:bg-white/10"
                                                    onPress={() => {
                                                        recipe.missing_items.forEach((item: string) => handleAdd(item));
                                                        alert(`Added ${recipe.missing_items.length} items to list!`);
                                                    }}
                                                >
                                                    Add Missing Items ({recipe.missing_items.length})
                                                </Button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {isChefTyping && (
                                <div className="flex justify-start">
                                    <div className="bg-black/5 dark:bg-white/10 px-4 py-2 rounded-full animate-pulse text-xs">
                                        Agent is thinking...
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="flex gap-2 mb-2 px-1 flex-wrap">
                            <Button
                                size="sm"
                                radius="full"
                                variant={useShoppingList ? "solid" : "bordered"}
                                color={useShoppingList ? "primary" : "default"}
                                onPress={() => setUseShoppingList(!useShoppingList)}
                                className="text-xs font-bold"
                            >
                                {useShoppingList ? "List ✅" : "No List"}
                            </Button>
                            <Button
                                size="sm"
                                radius="full"
                                variant={useDeals ? "solid" : "bordered"}
                                color={useDeals ? "secondary" : "default"}
                                onPress={() => setUseDeals(!useDeals)}
                                className="text-xs font-bold"
                            >
                                {useDeals ? "Deals ✅" : "No Deals"}
                            </Button>
                        </div>

                        {/* Chat Input Bar */}
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
                                placeholder="Ask Agent..."
                                value={chefMessage}
                                onChange={(e) => setChefMessage(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAskChef()}
                                classNames={{
                                    inputWrapper: "bg-black/5 dark:bg-white/10 border-black/20 dark:border-white/20 text-black dark:text-white"
                                }}
                            />
                            <Button isIconOnly color="secondary" onPress={() => handleAskChef()} isLoading={isChefTyping}>
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
