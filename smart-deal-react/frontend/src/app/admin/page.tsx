'use client';

import Navbar from '../../components/Navbar';
import { useState, useEffect } from 'react';
import { Tabs, Tab, Card, CardBody, Button, Progress, Spacer, Chip, CardHeader } from "@heroui/react";
import { uploadFile, getActiveDeals } from '../../lib/api';
import { motion } from 'framer-motion';
import DealCard from '../../components/DealCard';

export default function AdminPage() {
    const [selected, setSelected] = useState("upload");
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState("");
    const [deals, setDeals] = useState<any[]>([]);

    useEffect(() => {
        fetchDeals();
    }, []);

    const fetchDeals = async () => {
        try {
            const data = await getActiveDeals();
            if (data && data.deals) {
                setDeals(data.deals);
            }
        } catch (e) {
            console.error("Failed to load deals", e);
        }
    }

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;

        const file = e.target.files[0];
        setIsUploading(true);
        setUploadStatus("Processing with Gemini AI...");

        try {
            const result = await uploadFile(file);
            setUploadStatus(`Success! Extracted ${result.deal_count} deals.`);
            setDeals(result.deals);
            setTimeout(() => setSelected("dashboard"), 1500);
        } catch (error) {
            setUploadStatus("Error uploading file.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen pt-24 pb-12 px-6">
            <Navbar />
            <div className="max-w-7xl mx-auto">

                <div className="flex flex-col w-full">
                    <div className="flex justify-between items-center mb-8">
                        <div>
                            <h1 className="text-4xl font-black text-white mb-2">Admin Hub</h1>
                            <p className="text-white/50">Manage inventory and process flyers.</p>
                        </div>
                        <div className="bg-white/5 p-2 rounded-xl backdrop-blur-md border border-white/10">
                            {/* Clean Tabs */}
                            <Tabs
                                selectedKey={selected}
                                onSelectionChange={(key) => setSelected(key as string)}
                                aria-label="Admin Options"
                                color="secondary"
                                variant="light"
                                classNames={{
                                    tabList: "gap-4",
                                    cursor: "bg-white/10 shadow-none border border-white/10",
                                    tabContent: "font-bold text-white/70 group-data-[selected=true]:text-white"
                                }}
                            >
                                <Tab key="upload" title="📤 Upload Flyer" />
                                <Tab key="dashboard" title="📊 Live Dashboard" />
                            </Tabs>
                        </div>
                    </div>

                    {selected === 'upload' && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="w-full max-w-3xl mx-auto"
                        >
                            <Card className="min-h-[500px] bg-white/5 border-2 border-dashed border-white/20 hover:border-purple-500/50 transition-colors shadow-2xl">
                                <CardBody className="flex flex-col items-center justify-center text-center p-12">
                                    <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-purple-500 to-pink-500 flex items-center justify-center mb-6 shadow-lg shadow-purple-500/30">
                                        <div className="text-5xl text-white">☁️</div>
                                    </div>
                                    <h3 className="text-3xl font-bold text-white mb-4">Drop Flyer Here</h3>
                                    <p className="text-lg text-white/60 mb-8 max-w-md">
                                        Upload your supermarket PDF or image. <br />Gemini AI will extract products, prices, and discounts instantly.
                                    </p>

                                    <input
                                        type="file"
                                        id="file-upload"
                                        className="hidden"
                                        onChange={handleFileUpload}
                                        accept=".pdf,.jpg,.jpeg,.png"
                                    />
                                    <label htmlFor="file-upload">
                                        <Button
                                            as="span"
                                            size="lg"
                                            className="bg-white text-purple-900 font-bold px-12 py-8 text-xl shadow-xl hover:scale-105 transition-transform cursor-pointer"
                                        >
                                            Select File
                                        </Button>
                                    </label>

                                    {isUploading && (
                                        <div className="w-full max-w-sm mt-12 bg-white/5 p-4 rounded-xl border border-white/10 backdrop-blur-md">
                                            <div className="flex justify-between text-sm text-white/80 mb-2">
                                                <span>Extracting data...</span>
                                                <span className="animate-pulse">Processing</span>
                                            </div>
                                            <Progress
                                                size="sm"
                                                isIndeterminate
                                                classNames={{
                                                    indicator: "bg-gradient-to-r from-pink-500 to-purple-500",
                                                    track: "bg-white/10"
                                                }}
                                            />
                                        </div>
                                    )}
                                    {!isUploading && uploadStatus && (
                                        <div className="mt-8 px-6 py-3 bg-green-500/20 border border-green-500/30 text-green-200 rounded-full">
                                            {uploadStatus}
                                        </div>
                                    )}
                                </CardBody>
                            </Card>
                        </motion.div>
                    )}

                    {selected === 'dashboard' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                        >
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                                <Card className="bg-gradient-to-br from-purple-600 to-indigo-600 border-none shadow-xl text-white">
                                    <CardBody className="p-6">
                                        <p className="text-white/60 font-medium mb-1">Active Deals</p>
                                        <h2 className="text-5xl font-black">{deals.length}</h2>
                                    </CardBody>
                                </Card>
                                <Card className="bg-white/5 border border-white/10 backdrop-blur-md text-white">
                                    <CardBody className="p-6">
                                        <p className="text-white/60 font-medium mb-1">Total Savings</p>
                                        <h2 className="text-5xl font-black text-emerald-400">High</h2>
                                    </CardBody>
                                </Card>
                            </div>

                            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                                <span className="w-2 h-8 bg-pink-500 rounded-full" />
                                Extracted Products
                            </h2>

                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                                {deals.map((deal, idx) => (
                                    <DealCard key={idx} deal={deal} /> // No add button in admin view
                                ))}
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>
        </div>
    );
}
