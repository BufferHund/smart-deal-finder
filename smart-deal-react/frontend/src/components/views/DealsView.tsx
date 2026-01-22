'use client';

import { Card, CardBody, Button, Chip, Select, SelectItem, Tabs, Tab, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Switch, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Input, useDisclosure, CircularProgress } from "@heroui/react";
import { Search, ShoppingCart, Filter, Sparkles, TrendingUp, Store, Apple, Beef, Milk, Croissant, Beer, IceCream, SprayCan, Package, ScanLine, Upload, Globe, Lock } from "lucide-react";
import { useState, useEffect, useRef } from 'react';
import { getActiveDeals, addToShoppingList, uploadFile } from '../../lib/api';
import { motion, AnimatePresence } from "framer-motion";

// Store Metadata Helper (reused/simplified)
const getStoreColor = (store: string) => {
    const s = store.toLowerCase();
    if (s.includes('rewe')) return 'from-red-600 to-red-800';
    if (s.includes('lidl')) return 'from-blue-600 to-blue-800';
    if (s.includes('aldi')) return 'from-blue-500 to-blue-700';
    if (s.includes('edeka')) return 'from-yellow-500 to-yellow-600 text-black';
    return 'from-gray-700 to-gray-900';
};

// Category Gradient Helper
const getCategoryGradient = (category: string | undefined) => {
    switch (category) {
        case "Fruit & Veg": return "bg-gradient-to-br from-green-400 to-emerald-600";
        case "Meat & Fish": return "bg-gradient-to-br from-red-400 to-rose-600";
        case "Dairy": return "bg-gradient-to-br from-blue-300 to-cyan-500";
        case "Bakery": return "bg-gradient-to-br from-amber-300 to-orange-500";
        case "Drinks": return "bg-gradient-to-br from-violet-400 to-purple-600";
        case "Snacks": return "bg-gradient-to-br from-pink-400 to-fuchsia-600";
        case "Household": return "bg-gradient-to-br from-slate-400 to-gray-600";
        default: return "bg-gradient-to-br from-gray-300 to-slate-500";
    }
};

const CATEGORIES = ["All", "Fruit & Veg", "Meat & Fish", "Dairy", "Bakery", "Drinks", "Snacks", "Household"];
const STORES = ["All Stores", "Rewe", "Lidl", "Aldi", "Edeka", "Netto", "Penny"];

// Category Icon Helper
const getCategoryIcon = (category: string) => {
    switch (category) {
        case "Fruit & Veg": return <Apple className="w-16 h-16" />;
        case "Meat & Fish": return <Beef className="w-16 h-16" />;
        case "Dairy": return <Milk className="w-16 h-16" />;
        case "Bakery": return <Croissant className="w-16 h-16" />;
        case "Drinks": return <Beer className="w-16 h-16" />;
        case "Snacks": return <IceCream className="w-16 h-16" />;
        case "Household": return <SprayCan className="w-16 h-16" />;
        default: return <Package className="w-16 h-16" />;
    }
};

export default function DealsView() {
    const [deals, setDeals] = useState<any[]>([]);
    const [activeTab, setActiveTab] = useState("foryou");
    const [selectedStore, setSelectedStore] = useState("All Stores");
    const [selectedCategory, setSelectedCategory] = useState("All");
    const [loading, setLoading] = useState(true);
    const [dislikedFilter, setDislikedFilter] = useState<string[]>([]);
    // Demo mode removed per request

    // Scan Modal State
    const { isOpen, onOpen, onOpenChange } = useDisclosure();
    const [scanFile, setScanFile] = useState<File | null>(null);
    const [scanStore, setScanStore] = useState("");
    const [isPrivate, setIsPrivate] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [dealsData, prefData] = await Promise.all([
                getActiveDeals(),
                fetch('http://localhost:8000/api/agent/preferences').then(res => res.json()).catch(() => ({ disliked_items: [] }))
            ]);

            if (dealsData.deals) setDeals(dealsData.deals);
            if (prefData.disliked_items) setDislikedFilter(prefData.disliked_items);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async (deal: any) => {
        try {
            await addToShoppingList({ item: `${deal.product_name} (${deal.store})` });
            // Visual feedback could go here
        } catch (e) {
            console.error(e);
        }
    };

    // Filter Logic
    const filteredDeals = deals.filter(deal => {
        // Tab Filter
        // For "Recs", we might do random logic or simple heuristic for now.
        // Let's say Recs = Deals with "discount" (if we had it) or just show all for experimental purposes but randomized

        // Store Filter
        if (selectedStore !== "All Stores" && !deal.store.toLowerCase().includes(selectedStore.toLowerCase())) return false;

        // Category Filter
        if (selectedCategory !== "All" && deal.category !== selectedCategory) return false;

        return true;
    });

    const displayDeals = activeTab === 'foryou'
        ? filteredDeals.sort(() => 0.5 - Math.random()) // Shuffle for recommendations
        : filteredDeals; // Regular list

    return (
        <div className="p-4 pb-24 min-h-full">
            <header className="mb-6 pt-2">
                <div className="flex justify-between items-end mb-4">
                    <div>
                        <h1 className="text-3xl font-black text-black dark:text-white">Discover</h1>
                        <p className="text-black/50 dark:text-white/50 text-sm">Best deals near you</p>
                    </div>
                    {/* Debug / Demo Toggle Removed */}
                </div>

                {/* Main Tabs */}
                <Tabs
                    selectedKey={activeTab}
                    onSelectionChange={(k) => setActiveTab(k as string)}
                    variant="light"
                    classNames={{
                        tabList: "bg-black/5 dark:bg-white/5 p-1 rounded-full w-full max-w-xs",
                        cursor: "bg-gradient-to-tr from-pink-500 to-purple-500 rounded-full shadow-md",
                        tabContent: "text-black/70 dark:text-white/70 group-data-[selected=true]:text-white font-bold"
                    }}
                >
                    <Tab key="foryou" title={<div className="flex items-center gap-2"><Sparkles size={14} /> For You</div>} />
                    <Tab key="browse" title={<div className="flex items-center gap-2"><TrendingUp size={14} /> Browse</div>} />
                </Tabs>

                {/* Filters */}
                <div className="mt-4 space-y-3">
                    {/* Store Chips */}
                    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                        {STORES.map(store => (
                            <Chip
                                key={store}
                                variant={selectedStore === store ? "solid" : "bordered"}
                                color={selectedStore === store ? "secondary" : "default"}
                                className={`cursor-pointer border-black/20 dark:border-white/20 ${selectedStore === store ? '' : 'text-black/70 dark:text-white/70'}`}
                                onClick={() => setSelectedStore(store)}
                            >
                                {store}
                            </Chip>
                        ))}
                    </div>

                    {/* Category Dropdown (Simple Select) */}
                    <div className="flex gap-2">
                        <Select
                            label="Category"
                            size="sm"
                            variant="bordered"
                            placeholder="Select Category"
                            selectedKeys={[selectedCategory]}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            classNames={{
                                trigger: "border-black/20 dark:border-white/20 hover:border-black/40 dark:hover:border-white/40 bg-transparent text-black dark:text-white",
                                popoverContent: "bg-white dark:bg-[#1c1c1e] border border-black/10 dark:border-white/10",
                                value: "text-black dark:text-white"
                            }}
                        >
                            {CATEGORIES.map((cat) => (
                                <SelectItem key={cat} className="text-black dark:text-white">
                                    {cat}
                                </SelectItem>
                            ))}
                        </Select>
                    </div>
                </div>
            </header>

            {/* Content Grid */}
            <div className="grid grid-cols-2 gap-3">
                {loading ? (
                    // Skeleton
                    [...Array(4)].map((_, i) => (
                        <Card key={i} className="h-48 bg-white/5 animate-pulse border-none space-y-2 p-2">
                            <div className="h-24 bg-white/10 rounded-lg" />
                            <div className="h-4 w-3/4 bg-white/10 rounded" />
                            <div className="h-4 w-1/2 bg-white/10 rounded" />
                        </Card>
                    ))
                ) : displayDeals.length === 0 ? (
                    <div className="col-span-2 text-center text-white/30 py-12">
                        <Filter size={48} className="mx-auto mb-4 opacity-50" />
                        <p>No deals found for these filters.</p>
                    </div>
                ) : (
                    displayDeals.map((deal, i) => (
                        <motion.div
                            key={i}
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: i * 0.05 }}
                        >
                            <Card className="w-full bg-white dark:bg-[#1c1c1e] border-0 dark:border dark:border-white/5 h-full relative overflow-hidden group shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-500">
                                {/* Store Label */}
                                <div className={`absolute top-0 right-0 px-2 py-1 text-[10px] font-bold text-white bg-gradient-to-r ${getStoreColor(deal.store)} rounded-bl-lg z-10 uppercase tracking-wider`}>
                                    {deal.store}
                                </div>

                                {/* Placeholder Image Area - Colorful Gradients */}
                                <div className={`h-28 flex items-center justify-center relative overflow-hidden ${!deal.image_url ? getCategoryGradient(deal.category) : 'bg-gray-50 dark:bg-white/5'}`}>
                                    {deal.image_url ? (
                                        <img src={deal.image_url} alt={deal.product_name} className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="opacity-90 scale-110 rotate-[-10deg] drop-shadow-lg text-white">
                                            {getCategoryIcon(deal.category)}
                                        </div>
                                    )}
                                    <div className="absolute inset-0 bg-gradient-to-t from-white via-white/20 to-transparent dark:from-[#1c1c1e] dark:via-transparent dark:to-transparent opacity-90 dark:opacity-80" />
                                </div>

                                <CardBody className="pt-0 pb-4 px-3 flex flex-col justify-between h-[120px]">
                                    <div>
                                        <p className="text-xs text-secondary font-bold mb-1">{deal.category || 'Deal'}</p>
                                        <h3 className="text-sm font-semibold text-black dark:text-white line-clamp-2 leading-tight mb-2">
                                            {deal.product_name}
                                        </h3>
                                    </div>
                                    <div className="flex items-end justify-between">
                                        <div>
                                            {deal.original_price && <span className="text-xs text-white/40 line-through block">€{deal.original_price}</span>}
                                            <div className="flex items-baseline gap-0.5">
                                                <span className="text-lg font-black text-green-600 dark:text-green-400 p-0 m-0 leading-none">€{deal.price}</span>
                                                <span className="text-[10px] text-black/50 dark:text-white/50">{deal.unit}</span>
                                            </div>
                                        </div>
                                        <Button isIconOnly size="sm" className="bg-gray-100 dark:bg-white/10 hover:bg-black/5 dark:hover:bg-white text-black dark:text-white hover:text-black rounded-full transition-colors shadow-sm dark:shadow-none" onPress={() => handleAdd(deal)}>
                                            <ShoppingCart size={14} />
                                        </Button>
                                    </div>
                                </CardBody>
                            </Card>
                        </motion.div>
                    ))
                )}
            </div>
            {/* Scan FAB */}
            <motion.div
                className="fixed bottom-24 right-6 z-50"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
            >
                <Button
                    isIconOnly
                    className="w-14 h-14 rounded-full bg-gradient-to-tr from-pink-500 to-purple-500 text-white shadow-xl shadow-purple-500/40"
                    onPress={onOpen}
                >
                    <ScanLine size={24} />
                </Button>
            </motion.div>

            {/* Scan Modal */}
            <Modal isOpen={isOpen} onOpenChange={onOpenChange} backdrop="blur">
                <ModalContent className="bg-white dark:bg-[#1c1c1e] text-black dark:text-white border border-black/10 dark:border-white/10">
                    {(onClose) => (
                        <>
                            <ModalHeader className="flex flex-col gap-1">
                                <h2 className="text-xl font-bold flex items-center gap-2">
                                    <Upload size={20} /> Scan Brochure
                                </h2>
                                <p className="text-sm text-black/50 dark:text-white/50 font-normal">Extract deals instantly with AI.</p>
                            </ModalHeader>
                            <ModalBody>
                                <div
                                    className="border-2 border-dashed border-black/20 dark:border-white/20 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    {scanFile ? (
                                        <div className="text-center">
                                            <p className="font-bold text-green-600 dark:text-green-400 mb-1">{scanFile.name}</p>
                                            <p className="text-xs text-black/40 dark:text-white/40">{(scanFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="w-12 h-12 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center mb-3">
                                                <ScanLine className="text-black/60 dark:text-white/60" />
                                            </div>
                                            <p className="text-sm text-black/60 dark:text-white/60">Tap to upload or take photo</p>
                                        </>
                                    )}
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        className="hidden"
                                        accept="image/*,.pdf"
                                        capture="environment"
                                        onChange={(e) => e.target.files && setScanFile(e.target.files[0])}
                                    />
                                </div>

                                <Input
                                    label="Store Name"
                                    placeholder="e.g. Rewe, Lidl"
                                    variant="bordered"
                                    value={scanStore}
                                    onChange={(e) => setScanStore(e.target.value)}
                                    classNames={{ inputWrapper: "border-black/20 dark:border-white/20", label: "text-black/60 dark:text-white/60", input: "text-black dark:text-white" }}
                                />

                                <div className="bg-black/5 dark:bg-white/5 p-3 rounded-xl flex items-center justify-between border border-black/10 dark:border-white/10">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg ${isPrivate ? 'bg-red-500/20 text-red-500 dark:text-red-400' : 'bg-green-500/20 text-green-600 dark:text-green-400'}`}>
                                            {isPrivate ? <Lock size={18} /> : <Globe size={18} />}
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-black dark:text-white">{isPrivate ? 'Private' : 'Public'}</p>
                                            <p className="text-[10px] text-black/50 dark:text-white/50">
                                                {isPrivate ? 'Only visible to you' : 'Shared with community'}
                                            </p>
                                        </div>
                                    </div>
                                    <Switch
                                        size="sm"
                                        color="danger"
                                        isSelected={isPrivate}
                                        onValueChange={setIsPrivate}
                                    />
                                </div>
                            </ModalBody>
                            <ModalFooter>
                                <Button color="danger" variant="light" onPress={onClose}>
                                    Cancel
                                </Button>
                                <Button
                                    className="bg-gradient-to-tr from-pink-500 to-purple-500 text-white font-bold"
                                    isLoading={isUploading}
                                    onPress={async () => {
                                        if (!scanFile) return;
                                        setIsUploading(true);
                                        try {
                                            await uploadFile(scanFile, scanStore || "Unknown", false, isPrivate ? "private" : "public");
                                            onClose();
                                            setScanFile(null);
                                            setScanStore("");
                                            loadData(); // Refresh feed
                                        } catch (e) {
                                            alert("Upload failed");
                                        } finally {
                                            setIsUploading(false);
                                        }
                                    }}
                                >
                                    Start Scan
                                </Button>
                            </ModalFooter>
                        </>
                    )}
                </ModalContent>
            </Modal>
        </div>
    );
}
