'use client';

import { useState, useEffect, useCallback } from 'react';
import { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, Card, CardBody, Chip, Divider } from "@heroui/react";
import { MapPin, Navigation, AlertTriangle, CheckCircle, RefreshCw, Store, ArrowRight, X, Package, ArrowLeftRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { planRoute, getRouteAlternatives, confirmRoute, RoutePlanResult, StoreResult } from '../lib/api';
import dynamic from 'next/dynamic';

// Dynamic import for Leaflet map to avoid SSR issues
const MapPreview = dynamic(
    () => import('./LeafletMap'),
    { ssr: false, loading: () => <div className="h-48 w-full bg-gray-100 dark:bg-gray-800 animate-pulse rounded-xl" /> }
);

// Store brand colors
const getBrandColor = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes("rewe")) return "from-red-600 to-red-700";
    if (n.includes("lidl")) return "from-blue-600 to-blue-700";
    if (n.includes("aldi")) return "from-blue-700 to-blue-800";
    if (n.includes("edeka")) return "from-yellow-400 to-yellow-500";
    if (n.includes("penny")) return "from-red-500 to-red-600";
    if (n.includes("netto")) return "from-yellow-500 to-yellow-600";
    if (n.includes("kaufland")) return "from-red-600 to-red-700";
    return "from-gray-500 to-gray-600";
};

interface RouteAgentModalProps {
    isOpen: boolean;
    onClose: () => void;
    items: string[];
    userLocation: [number, number] | null;
    onRouteConfirmed?: (stores: string[]) => void;
}

type AgentStep = 'analyzing' | 'results' | 'warning' | 'alternatives' | 'complete';

interface Message {
    type: 'agent' | 'system';
    content: string;
    action?: React.ReactNode;
}

export default function RouteAgentModal({ isOpen, onClose, items, userLocation, onRouteConfirmed }: RouteAgentModalProps) {
    const [step, setStep] = useState<AgentStep>('analyzing');
    const [messages, setMessages] = useState<Message[]>([]);
    const [routePlan, setRoutePlan] = useState<RoutePlanResult | null>(null);
    const [skippedStores, setSkippedStores] = useState<string[]>([]);
    const [substitutions, setSubstitutions] = useState<{ original: string, replacement: string, store: string }[]>([]);
    const [missingItemIndex, setMissingItemIndex] = useState(0);
    const [alternatives, setAlternatives] = useState<any | null>(null);
    const [currentWarningStore, setCurrentWarningStore] = useState<StoreResult | null>(null);
    const [loading, setLoading] = useState(false);

    const addMessage = useCallback((msg: Message) => {
        setMessages(prev => [...prev, msg]);
    }, []);

    const startPlanning = useCallback(async () => {
        if (!userLocation) {
            addMessage({ type: 'system', content: '📍 Location required to plan route. Please enable location services.' });
            return;
        }

        setStep('analyzing');
        setMessages([]);
        addMessage({ type: 'agent', content: '🔍 Analyzing your shopping list...' });

        try {
            setLoading(true);
            const result = await planRoute(items, userLocation);
            setRoutePlan(result);

            if (result.status === 'no_deals') {
                addMessage({ type: 'agent', content: '📭 ' + result.message });
                return;
            }

            addMessage({
                type: 'agent',
                content: `✅ Found ${result.recommended_stores.length + result.not_recommended.length} stores with deals`
            });

            // Check for not recommended stores
            if (result.not_recommended.length > 0) {
                setTimeout(() => {
                    setCurrentWarningStore(result.not_recommended[0]);
                    setStep('warning');
                }, 500);
            } else if (result.items_not_found.length > 0) {
                setMissingItemIndex(0);
                fetchAlternatives(result.items_not_found[0], result);
                setStep('alternatives');
            } else {
                setStep('results');
            }
        } catch (error) {
            addMessage({ type: 'system', content: '❌ Error planning route. Please try again.' });
        } finally {
            setLoading(false);
        }
    }, [items, userLocation, addMessage]);

    useEffect(() => {
        if (isOpen && items.length > 0) {
            startPlanning();
        }
    }, [isOpen, items, startPlanning]);

    const handleSkipStore = () => {
        if (currentWarningStore) {
            setSkippedStores(prev => [...prev, currentWarningStore.store]);
            addMessage({
                type: 'agent',
                content: `⏭️ Skipped ${currentWarningStore.store}`
            });

            // Check for more warnings
            const remaining = routePlan?.not_recommended.filter(
                s => !skippedStores.includes(s.store) && s.store !== currentWarningStore.store
            );
            if (remaining && remaining.length > 0) {
                setCurrentWarningStore(remaining[0]);
            } else {
                setStep('results');
            }
        }
    };

    const handleKeepStore = () => {
        if (currentWarningStore) {
            addMessage({
                type: 'agent',
                content: `✓ Keeping ${currentWarningStore.store}`
            });

            const remaining = routePlan?.not_recommended.filter(
                s => !skippedStores.includes(s.store) && s.store !== currentWarningStore.store
            );
            if (remaining && remaining.length > 0) {
                setCurrentWarningStore(remaining[0]);
            } else {
                setStep('results');
            }
        }
    };

    const handleConfirmRoute = async () => {
        if (!routePlan) return;

        // Pass substitutions to confirmation
        const selectedStores = routePlan.recommended_stores
            .filter(s => !skippedStores.includes(s.store))
            .map(s => s.store);

        try {
            await confirmRoute(selectedStores, substitutions);
            setStep('complete');
            addMessage({
                type: 'agent',
                content: `🎉 Route confirmed! ${selectedStores.length} stops, saving €${routePlan.total_savings.toFixed(2)}`
            });
            onRouteConfirmed?.(selectedStores);
        } catch (error) {
            addMessage({ type: 'system', content: '❌ Error confirming route' });
        }
    };

    const fetchAlternatives = async (item: string, plan: RoutePlanResult) => {
        try {
            setLoading(true);
            const excluded = plan.not_recommended.map(s => s.store);
            const alts = await getRouteAlternatives(item, undefined, excluded);
            setAlternatives(alts);
            addMessage({
                type: 'agent',
                content: `🔍 Looking for alternatives for "${item}"...`
            });
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleSubstitute = (replacement: any) => {
        if (!routePlan) return;

        const original = routePlan.items_not_found[missingItemIndex];
        setSubstitutions(prev => [...prev, {
            original,
            replacement: replacement.product_name,
            store: replacement.store
        }]);

        addMessage({
            type: 'agent',
            content: `🔄 Switched "${original}" with "${replacement.product_name}"`
        });

        nextMissingItem();
    };

    const handleSkipSubstitution = () => {
        if (!routePlan) return;
        const original = routePlan.items_not_found[missingItemIndex];
        addMessage({
            type: 'agent',
            content: `⏭️ Skipped substitution for "${original}"`
        });
        nextMissingItem();
    };

    const nextMissingItem = () => {
        if (!routePlan) return;
        const nextIndex = missingItemIndex + 1;
        if (nextIndex < routePlan.items_not_found.length) {
            setMissingItemIndex(nextIndex);
            fetchAlternatives(routePlan.items_not_found[nextIndex], routePlan);
        } else {
            setStep('results');
        }
    };

    const openNavigation = (store: string) => {
        // Open Google Maps with the store name as destination
        const url = `https://www.google.com/maps/search/${encodeURIComponent(store + ' supermarket')}`;
        window.open(url, '_blank');
    };

    const renderStoreCard = (store: StoreResult, isRecommended: boolean = true) => (
        <Card
            key={store.store}
            className={`bg-gradient-to-r ${getBrandColor(store.store)} text-white mb-2`}
        >
            <CardBody className="p-3">
                <div className="flex justify-between items-start">
                    <div>
                        <h4 className="font-bold text-lg">{store.store}</h4>
                        <div className="flex gap-2 mt-1 flex-wrap">
                            <Chip size="sm" className="bg-white/20 text-white">
                                {store.match_count} items
                            </Chip>
                            <Chip size="sm" className="bg-white/20 text-white">
                                {store.distance_km.toFixed(1)} km
                            </Chip>
                            <Chip size="sm" className="bg-green-500 text-white">
                                Save €{store.total_savings.toFixed(2)}
                            </Chip>
                        </div>
                    </div>
                    {isRecommended && (
                        <Button
                            isIconOnly
                            size="sm"
                            className="bg-white/20 text-white"
                            onPress={() => openNavigation(store.store)}
                        >
                            <Navigation size={16} />
                        </Button>
                    )}
                </div>
                {store.matches && store.matches.length > 0 && (
                    <div className="mt-2 text-sm text-white/80">
                        {store.matches.slice(0, 3).map((m, i) => (
                            <span key={i}>
                                {m.product_name} €{m.price}
                                {i < Math.min(store.matches!.length - 1, 2) ? ' • ' : ''}
                            </span>
                        ))}
                        {store.matches.length > 3 && ` +${store.matches.length - 3} more`}
                    </div>
                )}
            </CardBody>
        </Card>
    );

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            size="lg"
            scrollBehavior="inside"
            classNames={{
                base: "bg-white dark:bg-gray-900",
                header: "border-b border-gray-200 dark:border-gray-700",
                body: "py-4",
                footer: "border-t border-gray-200 dark:border-gray-700"
            }}
        >
            <ModalContent>
                <ModalHeader className="flex items-center gap-2">
                    <MapPin className="text-blue-500" size={20} />
                    <span className="text-black dark:text-white">Smart Route Planner</span>
                    <Chip size="sm" color="primary" variant="flat">Agent</Chip>
                </ModalHeader>

                <ModalBody>
                    {/* Message History */}
                    <div className="space-y-3 mb-4">
                        <AnimatePresence>
                            {messages.map((msg, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`p-3 rounded-lg ${msg.type === 'agent'
                                        ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                                        }`}
                                >
                                    {msg.content}
                                    {msg.action}
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>

                    {/* Loading State */}
                    {loading && (
                        <div className="flex items-center justify-center py-8">
                            <RefreshCw className="animate-spin text-blue-500" size={24} />
                            <span className="ml-2 text-gray-600 dark:text-gray-400">Analyzing...</span>
                        </div>
                    )}

                    {/* Warning Step */}
                    {step === 'warning' && currentWarningStore && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-xl p-4"
                        >
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="text-orange-500 flex-shrink-0 mt-1" size={24} />
                                <div className="flex-1">
                                    <h4 className="font-semibold text-orange-800 dark:text-orange-200">
                                        Not recommended: {currentWarningStore.store}
                                    </h4>
                                    <p className="text-sm text-orange-700 dark:text-orange-300 mt-1">
                                        {currentWarningStore.reason}
                                    </p>
                                    <div className="flex gap-2 mt-3">
                                        <Button
                                            size="sm"
                                            color="warning"
                                            variant="flat"
                                            onPress={handleSkipStore}
                                        >
                                            Skip this store
                                        </Button>
                                        <Button
                                            size="sm"
                                            variant="bordered"
                                            className="border-orange-300 text-orange-700 dark:text-orange-300"
                                            onPress={handleKeepStore}
                                        >
                                            Go anyway
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Alternatives Step */}
                    {step === 'alternatives' && alternatives && (
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-xl p-4"
                        >
                            <div className="flex items-start gap-3">
                                <ArrowLeftRight className="text-purple-500 flex-shrink-0 mt-1" size={24} />
                                <div className="flex-1">
                                    <h4 className="font-semibold text-purple-800 dark:text-purple-200 mb-1">
                                        Item not found: {routePlan?.items_not_found[missingItemIndex]}
                                    </h4>
                                    <p className="text-sm text-purple-600 dark:text-purple-300 mb-3">
                                        We found these similar items at recommended stores:
                                    </p>

                                    <div className="space-y-2 mb-3 max-h-48 overflow-y-auto">
                                        {[...alternatives.same_product_alternatives, ...alternatives.same_category_alternatives].slice(0, 3).map((alt: any, i: number) => (
                                            <div key={i} className="flex justify-between items-center bg-white dark:bg-gray-800 p-2 rounded-lg border border-purple-100 dark:border-purple-900/50">
                                                <div>
                                                    <p className="font-bold text-sm text-black dark:text-white">{alt.product_name}</p>
                                                    <p className="text-[10px] text-gray-500">{alt.store} • {alt.match_type === 'same_product' ? 'Same Item' : 'Similar'}</p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-bold text-green-600 dark:text-green-400">€{alt.price}</span>
                                                    <Button size="sm" color="secondary" variant="flat" className="h-7 min-w-0 px-2" onPress={() => handleSubstitute(alt)}>
                                                        Replace
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <Button size="sm" variant="light" className="w-full text-purple-400" onPress={handleSkipSubstitution}>
                                        Don't replace, just skip
                                    </Button>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Results Step */}
                    {step === 'results' && routePlan && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                        >
                            <div className="mb-4">
                                <h4 className="font-semibold text-black dark:text-white mb-2 flex items-center gap-2">
                                    <Store size={18} />
                                    Recommended Route ({routePlan.route_order.length} stops)
                                </h4>
                                <div className="flex items-center gap-2 mb-3 flex-wrap">
                                    {routePlan.route_order.map((store, i) => (
                                        <div key={store} className="flex items-center">
                                            <Chip
                                                className={`bg-gradient-to-r ${getBrandColor(store)} text-white`}
                                            >
                                                {i + 1}. {store}
                                            </Chip>
                                            {i < routePlan.route_order.length - 1 && (
                                                <ArrowRight size={16} className="text-gray-400 mx-1" />
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="h-64 w-full rounded-xl overflow-hidden mb-4 border border-black/10 dark:border-white/10 relative z-0">
                                <MapPreview
                                    userPosition={userLocation || undefined}
                                    stores={routePlan.recommended_stores
                                        .filter(s => !skippedStores.includes(s.store) && s.lat && s.lng)
                                        .map(s => ({
                                            id: s.store,
                                            name: s.store,
                                            brand: s.store,
                                            lat: s.lat!,
                                            lng: s.lng!
                                        }))}
                                />
                            </div>

                            <Divider className="my-3" />

                            <div className="space-y-2">
                                {routePlan.recommended_stores
                                    .filter(s => !skippedStores.includes(s.store))
                                    .map(store => renderStoreCard(store))}
                            </div>

                            {routePlan.items_not_found.length > 0 && (
                                <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                                        <Package size={16} />
                                        No deals found for: {routePlan.items_not_found.join(', ')}
                                    </p>
                                </div>
                            )}

                            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                                <p className="text-lg font-bold text-green-700 dark:text-green-300">
                                    💰 Estimated total savings: €{routePlan.total_savings.toFixed(2)}
                                </p>
                            </div>
                        </motion.div>
                    )}

                    {/* Complete Step */}
                    {step === 'complete' && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-center py-8"
                        >
                            <CheckCircle className="text-green-500 mx-auto mb-4" size={64} />
                            <h3 className="text-xl font-bold text-black dark:text-white">Route Confirmed!</h3>
                            <p className="text-gray-600 dark:text-gray-400 mt-2">Happy shopping! 🛒</p>
                        </motion.div>
                    )}
                </ModalBody>

                <ModalFooter>
                    <Button variant="flat" onPress={onClose}>
                        {step === 'complete' ? 'Close' : 'Cancel'}
                    </Button>
                    {step === 'results' && (
                        <Button
                            color="primary"
                            onPress={handleConfirmRoute}
                            startContent={<Navigation size={16} />}
                        >
                            Confirm Route & Start
                        </Button>
                    )}
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
}
