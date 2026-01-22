'use client';

import { Card, CardBody, Button, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Input, useDisclosure, Tabs, Tab } from "@heroui/react";
import { Plus, CreditCard, Trash2, X, Camera, Receipt, Euro, Wallet as WalletIcon, Apple, Smartphone } from "lucide-react";
import { useState, useEffect, useRef } from 'react';
import { getCards, addCard, deleteCard, scanCard, getReceipts, scanReceipt, deleteReceipt } from '../../lib/api';
import { motion, AnimatePresence } from "framer-motion";
import QRCode from "react-qr-code";
import Barcode from "react-barcode";
import { ExternalLink } from "lucide-react";

// Store Metadata Helper with real links
const getStoreDetails = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes("rewe")) return {
        color: "bg-gradient-to-br from-[#CC071E] to-[#9a0516]",
        textColor: "text-white",
        web: "https://www.rewe.de",
        iosApp: "https://apps.apple.com/de/app/rewe/id519712591",
        androidApp: "https://play.google.com/store/apps/details?id=de.rewe.app"
    };
    if (n.includes("lidl")) return {
        color: "bg-gradient-to-br from-[#0050AA] to-[#003d82]",
        textColor: "text-white",
        web: "https://www.lidl.de",
        iosApp: "https://apps.apple.com/de/app/lidl-plus/id1419106306",
        androidApp: "https://play.google.com/store/apps/details?id=com.lidl.eci.lidlplus"
    };
    if (n.includes("aldi")) return {
        color: "bg-gradient-to-br from-[#0046AD] to-[#003380]",
        textColor: "text-white",
        web: "https://www.aldi-sued.de",
        iosApp: "https://apps.apple.com/de/app/aldi-s%C3%BCd/id1346120498",
        androidApp: "https://play.google.com/store/apps/details?id=de.aldisued.app"
    };
    if (n.includes("edeka")) return {
        color: "bg-gradient-to-br from-[#F7E600] to-[#d4c500]",
        textColor: "text-black",
        web: "https://www.edeka.de",
        iosApp: "https://apps.apple.com/de/app/edeka/id364967445",
        androidApp: "https://play.google.com/store/apps/details?id=de.edeka.edeka.android"
    };
    if (n.includes("dm")) return {
        color: "bg-gradient-to-br from-[#29166F] to-[#1c0f4d]",
        textColor: "text-white",
        web: "https://www.dm.de",
        iosApp: "https://apps.apple.com/de/app/dm-deutschland/id543557624",
        androidApp: "https://play.google.com/store/apps/details?id=de.dm_drogerie_markt.aktivekosmetik"
    };
    if (n.includes("rossmann")) return {
        color: "bg-gradient-to-br from-[#E2001A] to-[#b30015]",
        textColor: "text-white",
        web: "https://www.rossmann.de",
        iosApp: "https://apps.apple.com/de/app/rossmann/id536962909",
        androidApp: "https://play.google.com/store/apps/details?id=de.rossmann.app"
    };
    if (n.includes("penny")) return {
        color: "bg-gradient-to-br from-[#C40C29] to-[#9a0920]",
        textColor: "text-white",
        web: "https://www.penny.de",
        iosApp: "https://apps.apple.com/de/app/penny-coupons-angebote/id1426616097",
        androidApp: "https://play.google.com/store/apps/details?id=de.penny.pennyapp"
    };
    if (n.includes("netto")) return {
        color: "bg-gradient-to-br from-[#FFD600] to-[#ccab00]",
        textColor: "text-black",
        web: "https://www.netto-online.de",
        iosApp: "https://apps.apple.com/de/app/netto-app/id1079088044",
        androidApp: "https://play.google.com/store/apps/details?id=de.netto_online.app2"
    };
    if (n.includes("kaufland")) return {
        color: "bg-gradient-to-br from-[#E30613] to-[#b3050f]",
        textColor: "text-white",
        web: "https://www.kaufland.de",
        iosApp: "https://apps.apple.com/de/app/kaufland/id1508566635",
        androidApp: "https://play.google.com/store/apps/details?id=de.kaufland.app"
    };

    // Default
    return { color: "bg-gradient-to-br from-gray-600 to-gray-800", textColor: "text-white", web: null, iosApp: null, androidApp: null };
};

// Helper to detect platform and get correct app link
const getAppLink = (details: ReturnType<typeof getStoreDetails>) => {
    if (typeof navigator !== 'undefined' && /iPhone|iPad|iPod/i.test(navigator.userAgent)) {
        return details.iosApp;
    }
    if (typeof navigator !== 'undefined' && /Android/i.test(navigator.userAgent)) {
        return details.androidApp;
    }
    return details.web; // Fallback to web for desktop
};

export default function WalletView() {
    // Loyalty State
    const [cards, setCards] = useState<any[]>([]);
    const { isOpen, onOpen, onOpenChange } = useDisclosure();
    const [newStore, setNewStore] = useState("");
    const [newCode, setNewCode] = useState("");
    const [newFormat, setNewFormat] = useState("BARCODE");
    const [isSaving, setIsSaving] = useState(false);
    const [isScanning, setIsScanning] = useState(false);
    const [selectedCard, setSelectedCard] = useState<any>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Receipt State
    const [activeTab, setActiveTab] = useState("loyalty");
    const [receipts, setReceipts] = useState<any[]>([]);
    const [isScanningReceipt, setIsScanningReceipt] = useState(false);
    const receiptInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [cardsData, receiptsData] = await Promise.all([
                getCards(),
                getReceipts().catch(() => ({ receipts: [] })) // Fail safe
            ]);

            if (cardsData.cards) setCards(cardsData.cards);
            if (receiptsData.receipts) setReceipts(receiptsData.receipts);
        } catch (e) {
            console.error(e);
        }
    };

    // Loyalty Logic
    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setIsScanning(true);
            try {
                const data = await scanCard(file);
                if (data.store_name) setNewStore(data.store_name);
                if (data.card_number) setNewCode(data.card_number);
                if (data.card_format) setNewFormat(data.card_format);
            } catch (err) {
                alert("Could not scan card.");
            } finally {
                setIsScanning(false);
            }
        }
    };

    const handleAddCard = async () => {
        if (!newStore || !newCode) return;
        setIsSaving(true);
        try {
            const res = await addCard(newStore, newCode, newFormat);
            setCards(res.cards);
            onOpenChange();
            setNewStore("");
            setNewCode("");
            setNewFormat("BARCODE");
        } catch (e) {
            console.error(e);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDeleteCard = async (id: number) => {
        try {
            const res = await deleteCard(id);
            setCards(res.cards);
            if (selectedCard?.id === id) setSelectedCard(null);
        } catch (e) {
            console.error(e);
        }
    };

    // Receipt Logic
    const handleReceiptScan = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setIsScanningReceipt(true);
            try {
                const res = await scanReceipt(file);
                if (res.receipts) setReceipts(res.receipts);
            } catch (err) {
                alert("Receipt scan failed.");
            } finally {
                setIsScanningReceipt(false);
            }
        }
    };

    const handleDeleteReceipt = async (id: number) => {
        try {
            const res = await deleteReceipt(id);
            if (res.receipts) setReceipts(res.receipts);
        } catch (e) {
            console.error(e);
        }
    };

    // Calculate Expenses
    const totalSpent = receipts.reduce((sum, r) => sum + parseFloat(r.total_amount || 0), 0);
    const spendingByDate = receipts.slice(0, 10).map(r => ({
        date: r.purchase_date,
        amount: parseFloat(r.total_amount)
    })).reverse();

    return (
        <div className="p-4 space-y-6 pb-32 relative h-full flex flex-col">
            <header className="flex justify-between items-center mb-2 pt-2">
                <div>
                    <h1 className="text-3xl font-black text-black dark:text-white">Wallet</h1>
                    <p className="text-black/50 dark:text-white/50 text-sm">Cards & Expenses</p>
                </div>
                <div className="flex gap-2">
                    <Button isIconOnly className="bg-white/10 text-white rounded-full" onPress={() => setActiveTab(activeTab === 'loyalty' ? 'receipts' : 'loyalty')}>
                        {activeTab === 'loyalty' ? <Receipt size={20} /> : <CreditCard size={20} />}
                    </Button>
                    {activeTab === 'loyalty' && (
                        <Button isIconOnly className="bg-white/10 text-white rounded-full" onPress={onOpen}>
                            <Plus size={24} />
                        </Button>
                    )}
                </div>
            </header>

            <Tabs
                selectedKey={activeTab}
                onSelectionChange={(k) => setActiveTab(k as string)}
                variant="light"
                classNames={{
                    tabList: "bg-black/5 dark:bg-white/5 p-1 rounded-full",
                    cursor: "bg-black/10 dark:bg-white/20 rounded-full",
                    tabContent: "text-black/70 dark:text-white/70 group-data-[selected=true]:text-black dark:group-data-[selected=true]:text-white font-bold"
                }}
            >
                <Tab key="loyalty" title="Loyalty Cards" />
                <Tab key="receipts" title="Receipts & Finance" />
            </Tabs>

            <AnimatePresence mode="wait">
                {activeTab === 'loyalty' ? (
                    <motion.div
                        key="loyalty"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 overflow-y-auto"
                    >
                        {cards.map((card, i) => {
                            const details = getStoreDetails(card.store_name);
                            return (
                                <motion.div
                                    key={card.id}
                                    initial={{ scale: 0.9, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    transition={{ delay: i * 0.1 }}
                                >
                                    <Card
                                        isPressable
                                        className={`w-full h-48 ${details.color} border-none relative overflow-hidden`}
                                        onPress={() => setSelectedCard(card)}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-black/30" />
                                        <CardBody className="relative z-10 flex flex-col justify-between h-full p-6">
                                            <div className="flex justify-between items-start">
                                                <h3 className={`text-2xl font-black ${details.textColor} drop-shadow-md uppercase tracking-wide`}>{card.store_name}</h3>
                                                <div className="bg-white/20 p-2 rounded-full backdrop-blur-sm">
                                                    <CreditCard className={details.textColor} size={20} />
                                                </div>
                                            </div>
                                            <div>
                                                <p className={`${details.textColor} opacity-80 font-mono tracking-widest text-lg drop-shadow-sm truncate`}>
                                                    {card.card_number}
                                                </p>
                                            </div>
                                        </CardBody>
                                        <div className="absolute -bottom-8 -right-8 w-32 h-32 bg-white/10 rounded-full blur-xl" />
                                    </Card>
                                </motion.div>
                            );
                        })}
                        {cards.length === 0 && (
                            <div className="col-span-1 border-2 border-dashed border-white/10 rounded-2xl h-48 flex flex-col items-center justify-center text-white/30">
                                <Plus size={32} className="mb-2" />
                                <p>Add your first card</p>
                            </div>
                        )}
                    </motion.div>
                ) : (
                    <motion.div
                        key="receipts"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col space-y-4 overflow-y-auto"
                    >
                        {/* Expense Summary */}
                        <Card className="bg-gradient-to-r from-emerald-900 to-green-900 border-none">
                            <CardBody className="flex flex-row items-center justify-between">
                                <div>
                                    <p className="text-white/50 text-xs uppercase font-bold">Total Spent</p>
                                    <h2 className="text-4xl font-black text-white">€{totalSpent.toFixed(2)}</h2>
                                </div>
                                <div className="p-3 bg-white/10 rounded-full">
                                    <Euro size={24} className="text-green-400" />
                                </div>
                            </CardBody>
                        </Card>

                        {/* Scan Button */}
                        <div className="grid grid-cols-1">
                            <input
                                type="file"
                                ref={receiptInputRef}
                                className="hidden"
                                accept="image/*"
                                capture="environment"
                                onChange={handleReceiptScan}
                            />
                            <Button
                                className="bg-white text-black font-bold h-12"
                                startContent={<Camera size={20} />}
                                isLoading={isScanningReceipt}
                                onPress={() => receiptInputRef.current?.click()}
                            >
                                Scan New Receipt
                            </Button>
                        </div>

                        {/* Recent Receipts List */}
                        <div className="space-y-2">
                            <h3 className="text-black/50 dark:text-white/50 text-sm font-bold uppercase">Recent Transactions</h3>
                            {receipts.length === 0 ? (
                                <p className="text-black/30 dark:text-white/30 text-center py-8">No receipts scanned yet.</p>
                            ) : (
                                receipts.map((r, i) => (
                                    <div key={r.id || i} className="bg-white dark:bg-white/5 p-3 rounded-xl border border-black/5 dark:border-white/5 shadow-sm dark:shadow-none">
                                        <div className="flex justify-between items-center">
                                            <div className="flex flex-col">
                                                <span className="font-bold text-black dark:text-white">{r.store_name}</span>
                                                <span className="text-xs text-black/50 dark:text-white/50">{r.purchase_date}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-mono text-green-600 dark:text-green-400 font-bold">-€{r.total_amount}</span>
                                                <Button isIconOnly size="sm" variant="light" color="danger" onPress={() => handleDeleteReceipt(r.id)}>
                                                    <Trash2 size={16} />
                                                </Button>
                                            </div>
                                        </div>
                                        {/* Items List */}
                                        {r.items && r.items.length > 0 && (
                                            <div className="mt-2 pt-2 border-t border-black/5 dark:border-white/5">
                                                <p className="text-xs text-black/40 dark:text-white/40 mb-1">Items:</p>
                                                <div className="flex flex-wrap gap-1">
                                                    {r.items.slice(0, 5).map((item: string, idx: number) => (
                                                        <span key={idx} className="text-xs bg-black/5 dark:bg-white/5 px-2 py-0.5 rounded-full text-black/70 dark:text-white/70">{item}</span>
                                                    ))}
                                                    {r.items.length > 5 && (
                                                        <span className="text-xs text-black/40 dark:text-white/40">+{r.items.length - 5} more</span>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Quick Pay Footer */}
            <div className="fixed bottom-24 left-4 right-4 h-16 bg-white/80 dark:bg-[#1c1c1e]/80 backdrop-blur-md rounded-2xl border border-black/10 dark:border-white/10 flex items-center justify-evenly p-2 z-50 shadow-lg dark:shadow-none">
                <Button className="flex-1 bg-black text-white h-full rounded-xl mr-2 gap-2 font-semibold">
                    <Apple size={20} /> Pay
                </Button>
                <div className="w-px h-8 bg-black/10 dark:bg-white/10" />
                <Button className="flex-1 bg-white text-black h-full rounded-xl ml-2 gap-2 font-semibold border border-black/10 dark:border-transparent">
                    <span className="font-bold text-blue-500">G</span> Pay
                </Button>
            </div>

            {/* Add Card Modal */}
            <Modal isOpen={isOpen} onOpenChange={onOpenChange} backdrop="blur">
                <ModalContent className="bg-white dark:bg-[#1c1c1e] text-black dark:text-white border border-black/10 dark:border-white/10">
                    {(onClose) => (
                        <>
                            <ModalHeader>Add Loyalty Card</ModalHeader>
                            <ModalBody>
                                <div className="flex justify-center mb-4">
                                    <input type="file" ref={fileInputRef} className="hidden" accept="image/*" capture="environment" onChange={handleFileChange} />
                                    <Button color="secondary" variant="flat" startContent={<Camera size={20} />} onPress={() => fileInputRef.current?.click()} isLoading={isScanning}>
                                        Scan / Upload
                                    </Button>
                                </div>
                                <Input label="Store Name" value={newStore} onChange={(e) => setNewStore(e.target.value)} variant="bordered" classNames={{ inputWrapper: "border-black/20 dark:border-white/20", input: "text-black dark:text-white" }} />
                                <Input label="Card Number" value={newCode} onChange={(e) => setNewCode(e.target.value)} variant="bordered" classNames={{ inputWrapper: "border-black/20 dark:border-white/20", input: "text-black dark:text-white" }} />
                            </ModalBody>
                            <ModalFooter>
                                <Button color="danger" variant="light" onPress={onClose}>Cancel</Button>
                                <Button color="primary" onPress={handleAddCard} isLoading={isSaving}>Save</Button>
                            </ModalFooter>
                        </>
                    )}
                </ModalContent>
            </Modal>

            {/* Detail Modal */}
            <AnimatePresence>
                {selectedCard && (
                    <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[60] bg-black/90 backdrop-blur-md flex items-center justify-center p-6"
                        onClick={() => setSelectedCard(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}
                            className="bg-white rounded-3xl overflow-hidden w-full max-w-sm"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {(() => {
                                const details = getStoreDetails(selectedCard.store_name);
                                return (
                                    <>
                                        <div className={`h-28 ${details.color} w-full flex items-center justify-center relative`}>
                                            <h2 className="text-3xl font-black text-white drop-shadow-md">{selectedCard.store_name}</h2>
                                            <Button isIconOnly size="sm" className="absolute top-4 right-4 bg-white/20 text-white rounded-full" onPress={() => setSelectedCard(null)}><X size={16} /></Button>

                                            {/* Open App Button */}
                                            {(details.iosApp || details.web) && (
                                                <Button
                                                    size="sm"
                                                    className="absolute bottom-4 right-4 bg-white text-black font-bold shadow-lg"
                                                    startContent={<ExternalLink size={16} />}
                                                    onPress={() => {
                                                        const link = getAppLink(details);
                                                        if (link) window.open(link, '_blank');
                                                    }}
                                                >
                                                    Open App
                                                </Button>
                                            )}
                                        </div>
                                    </>
                                );
                            })()}
                            <div className="p-8 flex flex-col items-center">
                                {selectedCard.card_format === 'QR' ? (
                                    <div className="p-2 bg-white shadow-inner border border-gray-100 rounded-xl mb-4">
                                        <QRCode value={selectedCard.card_number} size={180} />
                                    </div>
                                ) : (
                                    <div className="mb-4">
                                        <Barcode value={selectedCard.card_number} width={2} height={80} displayValue={false} />
                                    </div>
                                )}
                                <p className="text-2xl font-mono font-bold">{selectedCard.card_number}</p>
                                <Button color="danger" variant="flat" className="mt-8 w-full" startContent={<Trash2 size={18} />} onPress={() => handleDeleteCard(selectedCard.id)}>Delete</Button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div >
    );
}
