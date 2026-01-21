'use client';

import { Card, CardBody, CardFooter, Image, Button, Chip } from "@heroui/react";
import { motion } from "framer-motion";

interface DealCardProps {
    deal: any;
    onAdd?: (item: string) => void;
}

export default function DealCard({ deal, onAdd }: DealCardProps) {
    return (
        <motion.div
            whileHover={{ y: -5 }}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="h-full"
        >
            <Card className="h-full border-0 bg-white/5 backdrop-blur-md border-white/10 text-white shadow-xl hover:bg-white/10 transition-colors cursor-pointer group hover:shadow-2xl hover:shadow-purple-500/20">
                <CardBody className="p-0 relative overflow-hidden">
                    {/* Discount Badge */}
                    {deal.discount && (
                        <div className="absolute top-2 right-2 z-20">
                            <Chip
                                classNames={{
                                    base: "bg-gradient-to-br from-pink-500 to-red-600 border border-white/20 shadow-lg",
                                    content: "text-white font-bold drop-shadow-sm"
                                }}
                                size="sm"
                            >
                                {deal.discount}
                            </Chip>
                        </div>
                    )}

                    {/* Image Area */}
                    <div className="relative h-48 w-full overflow-hidden bg-gray-900 group-hover:opacity-90 transition-opacity">
                        {deal.image_url ? (
                            <Image
                                src={deal.image_url}
                                alt={deal.product}
                                className="object-cover w-full h-full scale-100 group-hover:scale-110 transition-transform duration-500"
                                removeWrapper
                            />
                        ) : (
                            <div className="w-full h-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                                <span className="text-5xl filter grayscale group-hover:grayscale-0 transition-all duration-300">🛒</span>
                            </div>
                        )}
                        {/* Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10" />
                    </div>

                    {/* Content */}
                    <div className="p-4 relative z-10 -mt-12">
                        <h3 className="font-bold text-lg text-white leading-tight min-h-[3rem] line-clamp-2 drop-shadow-md">
                            {deal.product}
                        </h3>
                        <div className="mt-3 flex items-end justify-between">
                            <div className="flex flex-col">
                                <span className="text-xs text-white/60 font-medium uppercase tracking-wider">{deal.unit_price || 'Great Deal'}</span>
                                <span className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">
                                    {deal.price}
                                </span>
                            </div>
                        </div>
                    </div>
                </CardBody>

                {onAdd && (
                    <CardFooter className="p-3 pt-0">
                        <Button
                            size="md"
                            fullWidth
                            className="bg-white/10 hover:bg-white/20 text-white font-semibold backdrop-blur-sm border border-white/10 shadow-lg group-hover:bg-purple-600/80 group-hover:border-purple-500/50 transition-all"
                            onPress={() => onAdd(deal.product)}
                        >
                            Add to List ➕
                        </Button>
                    </CardFooter>
                )}
            </Card>
        </motion.div>
    );
}
