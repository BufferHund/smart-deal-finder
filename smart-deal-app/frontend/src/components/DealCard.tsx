'use client';

import { Card, CardBody, CardFooter, Image, Button, Chip } from "@heroui/react";
import { motion } from "framer-motion";
import { ShoppingCart, Plus } from "lucide-react";

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
                                    base: "bg-red-600 border border-white/20 shadow-sm",
                                    content: "text-white font-bold text-xs"
                                }}
                                size="sm"
                            >
                                {deal.discount}
                            </Chip>
                        </div>
                    )}

                    {/* Store Badge */}
                    {deal.store && (
                        <div className="absolute top-2 left-2 z-20">
                            <Chip
                                classNames={{
                                    base: "bg-black/80 backdrop-blur-md border border-white/10",
                                    content: "text-white/90 text-[10px] font-bold uppercase tracking-wider"
                                }}
                                size="sm"
                            >
                                {deal.store}
                            </Chip>
                        </div>
                    )}

                    {/* Image Area */}
                    <div className="relative h-48 w-full overflow-hidden bg-gray-900 group-hover:opacity-90 transition-opacity">
                        {deal.image_url ? (
                            <Image
                                src={deal.image_url}
                                alt={deal.product_name || deal.product}
                                className="object-cover w-full h-full scale-100 group-hover:scale-110 transition-transform duration-500"
                                removeWrapper
                            />
                        ) : (
                            <div className="w-full h-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                                <ShoppingCart className="w-12 h-12 text-gray-500 group-hover:text-white transition-colors" />
                            </div>
                        )}
                        {/* Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10" />
                    </div>

                    {/* Content */}
                    <div className="p-4 relative z-10 -mt-12">
                        <h3 className="font-bold text-lg text-white leading-tight min-h-[3rem] line-clamp-2 drop-shadow-md">
                            {deal.product_name || deal.product || "Unknown Product"}
                        </h3>
                        <div className="mt-3 flex items-end justify-between">
                            <div className="flex flex-col">
                                <span className="text-xs text-white/60 font-medium uppercase tracking-wider">{deal.unit || deal.unit_price || ''}</span>
                                <span className="text-2xl font-black text-white">
                                    {deal.price} €
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
                            onPress={() => onAdd(deal.product_name || deal.product)}
                        >
                            <Plus size={16} className="mr-1" /> Add to List
                        </Button>
                    </CardFooter>
                )}
            </Card>
        </motion.div>
    );
}
