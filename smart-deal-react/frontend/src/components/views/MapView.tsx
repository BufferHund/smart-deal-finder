'use client';

// Dynamic import for Leaflet to avoid SSR issues
import dynamic from 'next/dynamic';
import { useMemo, useState, useEffect } from 'react';
import { Card, CardBody, Button, Chip } from "@heroui/react";
import { MapPin, Navigation, Store, ChevronUp, ChevronDown, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Store brand colors
const getBrandColor = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes("rewe")) return "bg-[#CC071E]";
    if (n.includes("lidl")) return "bg-[#0050AA]";
    if (n.includes("aldi")) return "bg-[#0046AD]";
    if (n.includes("edeka")) return "bg-[#F7E600] text-black";
    if (n.includes("penny")) return "bg-[#C40C29]";
    if (n.includes("netto")) return "bg-[#FFD600] text-black";
    if (n.includes("kaufland")) return "bg-[#E30613]";
    if (n.includes("dm")) return "bg-[#29166F]";
    if (n.includes("rossmann")) return "bg-[#E2001A]";
    return "bg-gray-600";
};

export default function MapView() {
    const [stores, setStores] = useState<any[]>([]);
    const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
    const [isListExpanded, setIsListExpanded] = useState(true);
    const [permissionStatus, setPermissionStatus] = useState<'prompt' | 'granted' | 'denied' | 'loading'>('loading');
    const [loading, setLoading] = useState(false);

    // Leaflet map must be client-side only - passing props through dynamic import
    const MapComponent = useMemo(() => dynamic(
        () => import('../../components/LeafletMap'),
        {
            loading: () => <div className="h-full w-full flex items-center justify-center text-black/50 dark:text-white/50">Loading Map...</div>,
            ssr: false
        }
    ), []);

    // Check geolocation permission on mount
    useEffect(() => {
        checkPermission();
    }, []);

    const checkPermission = async () => {
        if (!navigator.geolocation) {
            setPermissionStatus('denied');
            return;
        }

        // Check permission status if available
        if (navigator.permissions) {
            try {
                const result = await navigator.permissions.query({ name: 'geolocation' });
                setPermissionStatus(result.state as 'prompt' | 'granted' | 'denied');

                if (result.state === 'granted') {
                    requestLocation();
                }
            } catch (e) {
                // Fallback: just try to get location
                setPermissionStatus('prompt');
            }
        } else {
            setPermissionStatus('prompt');
        }
    };

    const requestLocation = () => {
        setLoading(true);
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const loc: [number, number] = [pos.coords.latitude, pos.coords.longitude];
                setUserLocation(loc);
                setPermissionStatus('granted');
                fetchNearbyStores(loc[0], loc[1]);
            },
            (err) => {
                console.error("Location denied:", err);
                setPermissionStatus('denied');
                setLoading(false);
                // Fallback to Berlin
                fetchNearbyStores(52.5200, 13.4050);
            }
        );
    };

    const fetchNearbyStores = async (lat: number, lng: number) => {
        try {
            const query = `
                [out:json];
                (
                  node["shop"="supermarket"](around:2000, ${lat}, ${lng});
                  node["shop"="convenience"](around:2000, ${lat}, ${lng});
                  way["shop"="supermarket"](around:2000, ${lat}, ${lng});
                );
                out center;
            `;
            const url = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query.replace(/\s+/g, ' '))}`;

            const res = await fetch(url);
            const data = await res.json();

            const foundStores = data.elements.map((el: any) => {
                const storeLat = el.lat || el.center?.lat;
                const storeLng = el.lon || el.center?.lon;
                const distance = calculateDistance(lat, lng, storeLat, storeLng);
                return {
                    id: el.id,
                    name: el.tags?.name || "Supermarket",
                    brand: el.tags?.brand || el.tags?.name || "Unknown",
                    lat: storeLat,
                    lng: storeLng,
                    distance: distance,
                    address: el.tags?.["addr:street"] || ""
                };
            }).sort((a: any, b: any) => a.distance - b.distance);

            setStores(foundStores);
        } catch (e) {
            console.error("Failed to fetch stores", e);
        } finally {
            setLoading(false);
        }
    };

    // Calculate distance in km
    const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    };

    const formatDistance = (km: number) => {
        if (km < 1) return `${Math.round(km * 1000)}m`;
        return `${km.toFixed(1)}km`;
    };

    return (
        <div className="h-screen w-full fixed inset-0 z-0">
            <MapComponent userPosition={userLocation ?? undefined} stores={stores} />

            {/* Header Overlay */}
            <div className="absolute top-12 left-4 right-4 z-[400] pointer-events-none">
                <div className="bg-white/90 dark:bg-black/60 backdrop-blur-md p-4 rounded-2xl border border-black/10 dark:border-white/10 pointer-events-auto shadow-lg">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-xl font-bold text-black dark:text-white flex items-center gap-2">
                                <MapPin size={20} className="text-red-500" /> Store Locator
                            </h1>
                            <p className="text-black/60 dark:text-white/60 text-xs">
                                {stores.length > 0 ? `${stores.length} stores nearby` : "Finding stores..."}
                            </p>
                        </div>
                        {permissionStatus === 'prompt' && (
                            <Button
                                size="sm"
                                className="bg-blue-500 text-white font-bold"
                                onPress={requestLocation}
                                isLoading={loading}
                            >
                                Enable Location
                            </Button>
                        )}
                        {permissionStatus === 'denied' && (
                            <Chip size="sm" color="danger" variant="flat">Location Denied</Chip>
                        )}
                    </div>
                </div>
            </div>

            {/* Store List Panel */}
            <motion.div
                className="absolute bottom-20 left-0 right-0 z-[400] pointer-events-auto"
                initial={{ y: 100 }}
                animate={{ y: 0 }}
            >
                <div className="mx-4 bg-white/95 dark:bg-[#1c1c1e]/95 backdrop-blur-md rounded-t-2xl border border-black/10 dark:border-white/10 shadow-xl overflow-hidden">
                    {/* Toggle Header */}
                    <div
                        className="flex justify-between items-center px-4 py-3 cursor-pointer"
                        onClick={() => setIsListExpanded(!isListExpanded)}
                    >
                        <span className="text-sm font-bold text-black dark:text-white flex items-center gap-2">
                            <Store size={16} /> Nearby Stores
                        </span>
                        <Button isIconOnly size="sm" variant="light" className="text-black/50 dark:text-white/50">
                            {isListExpanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
                        </Button>
                    </div>

                    {/* Store List */}
                    <AnimatePresence>
                        {isListExpanded && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="overflow-hidden"
                            >
                                <div className="max-h-[200px] overflow-y-auto space-y-2 px-4 pb-4">
                                    {loading ? (
                                        <div className="text-center py-4 text-black/50 dark:text-white/50 text-sm">
                                            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
                                            Searching nearby stores...
                                        </div>
                                    ) : stores.length === 0 ? (
                                        <div className="text-center py-4 text-black/50 dark:text-white/50 text-sm">
                                            No stores found nearby
                                        </div>
                                    ) : (
                                        stores.slice(0, 10).map((store, i) => (
                                            <Card
                                                key={store.id || i}
                                                isPressable
                                                className="bg-black/5 dark:bg-white/5 border-none shadow-none"
                                                onPress={() => {
                                                    window.open(`https://www.google.com/maps/dir/?api=1&destination=${store.lat},${store.lng}`, '_blank');
                                                }}
                                            >
                                                <CardBody className="py-2 px-3 flex flex-row items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                        <div className={`w-10 h-10 rounded-lg ${getBrandColor(store.name)} flex items-center justify-center`}>
                                                            <Store size={18} className="text-white" />
                                                        </div>
                                                        <div>
                                                            <p className="font-bold text-black dark:text-white text-sm">{store.name}</p>
                                                            <p className="text-black/50 dark:text-white/50 text-xs">{store.address || store.brand}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Chip size="sm" variant="flat" className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs">
                                                            {formatDistance(store.distance)}
                                                        </Chip>
                                                        <ExternalLink size={14} className="text-black/30 dark:text-white/30" />
                                                    </div>
                                                </CardBody>
                                            </Card>
                                        ))
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </div>
    );
}
