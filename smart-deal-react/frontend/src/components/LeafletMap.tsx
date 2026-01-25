'use client';

import { MapContainer, TileLayer, Marker, Popup, Circle, useMap, useMapEvents } from 'react-leaflet';
import { debounce } from 'lodash';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect, useState } from 'react';
import { Button } from "@heroui/react";
import { useTheme } from "next-themes";
import { Navigation } from "lucide-react";

// Fix Leaflet default icon issue in Next.js
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;

const DefaultIcon = L.icon({
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const StoreIcon = L.icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3759/3759247.png',
    iconSize: [32, 32],
    iconAnchor: [16, 32]
});

// Component to handle map center updates
function MapCenterUpdater({ position }: { position: [number, number] }) {
    const map = useMap();
    useEffect(() => {
        map.setView(position, map.getZoom());
    }, [position, map]);
    return null;
}

// Component to handle dynamic fetching
function MapEvents({ onMoveEnd }: { onMoveEnd: (center: L.LatLng) => void }) {
    const map = useMapEvents({
        moveend: () => {
            onMoveEnd(map.getCenter());
        },
    });
    return null;
}

interface LeafletMapProps {
    userPosition?: [number, number];
    stores?: any[];
    onStoresUpdate?: (stores: any[]) => void;
}

export default function LeafletMap({ userPosition, stores: externalStores, onStoresUpdate }: LeafletMapProps) {
    const [position, setPosition] = useState<[number, number]>(userPosition || [52.5200, 13.4050]);
    const [userFound, setUserFound] = useState(false);
    const [stores, setStores] = useState<any[]>(externalStores || []);
    const [loading, setLoading] = useState(false);
    const { theme, resolvedTheme } = useTheme();

    // Sync with external position
    useEffect(() => {
        if (userPosition) {
            setPosition(userPosition);
            setUserFound(true);
        }
    }, [userPosition]);

    // Sync with external stores
    useEffect(() => {
        if (externalStores) {
            setStores(externalStores);
        }
    }, [externalStores]);

    const fetchStores = async (lat: number, lng: number) => {
        setLoading(true);
        try {
            // Overpass API Query
            const query = `
                [out:json];
                (
                  node["shop"="supermarket"](around:2000, ${lat}, ${lng});
                  node["shop"="convenience"](around:2000, ${lat}, ${lng});
                  way["shop"="supermarket"](around:2000, ${lat}, ${lng});
                );
                out center;
            `;
            const url = `https://overpass-api.de/api/interpreter?data=${src_code_encode(query)}`;

            const res = await fetch(url);
            const data = await res.json();

            const foundStores = data.elements.map((el: any) => {
                const lat = el.lat || el.center.lat;
                const lon = el.lon || el.center.lon;
                return {
                    id: el.id,
                    name: el.tags.name || "Supermarket",
                    brand: el.tags.brand || el.tags.name || "Unknown",
                    lat: lat,
                    lng: lon
                };
            });

            setStores(foundStores);
        } catch (e) {
            console.error("Failed to fetch stores", e);
        } finally {
            setLoading(false);
        }
    };

    // Helper to encode query
    const src_code_encode = (str: string) => {
        return encodeURIComponent(str.replace(/\s+/g, ' '));
    }

    const handleLocate = () => {
        setLoading(true);
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const newPos: [number, number] = [pos.coords.latitude, pos.coords.longitude];
                    setPosition(newPos);
                    setUserFound(true);
                    fetchStores(newPos[0], newPos[1]);
                    setLoading(false);
                },
                (err) => {
                    console.error("Location access denied", err);
                    setLoading(false);
                    alert("Could not access location. Please enable permissions.");
                }
            );
        } else {
            alert("Geolocation is not supported by your browser");
            setLoading(false);
        }
    };

    return (
        <div className="h-full w-full relative">
            <MapContainer center={position} zoom={14} style={{ height: "100%", width: "100%" }} zoomControl={false}>
                <MapCenterUpdater position={position} />
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url={resolvedTheme === 'dark'
                        ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    }
                />
                <MapEvents
                    onMoveEnd={debounce((center: L.LatLng) => {
                        fetchStores(center.lat, center.lng);
                    }, 1000)}
                />

                <Circle center={position} radius={500} pathOptions={{ fillColor: 'blue', fillOpacity: 0.1, color: 'blue', opacity: 0.3 }} />

                <Marker position={position}>
                    <Popup>
                        📍 You are here
                    </Popup>
                </Marker>

                {stores.map((store, i) => (
                    <Marker key={i} position={[store.lat, store.lng]}>
                        <Popup>
                            <div className="font-bold">{store.name}</div>
                            <div className="text-gray-500 text-xs">{store.brand}</div>
                            {/* Random deal count for demo effect, since we don't map real store IDs to our DB yet */}
                            <div className="text-green-600 font-bold mt-1">
                                {Math.floor(Math.random() * 20)} Active Deals
                            </div>
                            <a href={`https://www.google.com/maps/dir/?api=1&destination=${store.lat},${store.lng}`} target="_blank" className="text-blue-500 text-xs mt-1 block">
                                Navigate &gt;
                            </a>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>

            {/* Locate Me FAB */}
            <Button
                isIconOnly
                className="absolute bottom-6 right-6 z-[400] bg-white dark:bg-[#1c1c1e] text-black dark:text-white shadow-lg rounded-full w-12 h-12"
                onPress={handleLocate}
            >
                <Navigation size={20} className={loading ? "animate-spin" : ""} />
            </Button>

            {loading && (
                <div className="absolute top-20 left-1/2 transform -translate-x-1/2 bg-black/60 text-white px-4 py-2 rounded-full backdrop-blur-md z-[500] text-sm flex items-center gap-2">
                    <div className="animate-spin h-3 w-3 border-2 border-white border-t-transparent rounded-full" />
                    Searching area...
                </div>
            )}
        </div>
    );
}
