'use client';

import { useState, useRef, useEffect } from 'react';
import {
    Modal,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalFooter,
    Button,
    Input,
    ScrollShadow
} from "@heroui/react";
import { chatWithChef } from '../lib/api';
import { motion } from 'framer-motion';
import { Lightbulb, Clock, ChefHat } from 'lucide-react';

interface ChatInterfaceProps {
    isOpen: boolean;
    onOpenChange: () => void;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    type?: 'text' | 'menu' | 'recipe';
    data?: any;
}

export default function ChatInterface({ isOpen, onOpenChange }: ChatInterfaceProps) {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: "Bonjour! I'm your AI Budget Chef. Need a menu suggestion or a recipe?", type: 'text' }
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsLoading(true);

        try {
            const response = await chatWithChef(userMsg);
            // Determine content based on type
            let content = "";
            if (response.type === 'text') {
                content = response.data;
            } else if (response.type === 'menu') {
                content = "Here is a menu suggestion for you based on the deals:";
            } else if (response.type === 'recipe') {
                content = "Here is the recipe you asked for:";
            }

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: content,
                type: response.type,
                data: response.data
            }]);
        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I'm having trouble reaching the kitchen. Please try again." }]);
        } finally {
            setIsLoading(false);
        }
    };

    const renderContent = (msg: Message) => {
        if (msg.type === 'menu' && msg.data) {
            const menu = msg.data;
            return (
                <div className="bg-white/10 p-4 rounded-xl border border-white/10 mt-2">
                    <h3 className="text-xl font-bold text-emerald-300 mb-1">{menu.name}</h3>
                    <p className="italic text-white/80 mb-3 text-sm">{menu.description}</p>

                    <div className="bg-black/20 p-3 rounded-lg mb-3">
                        <p className="text-xs text-white/50 uppercase tracking-widest font-bold mb-1">Key Ingredients Used</p>
                        <div className="flex flex-wrap gap-2">
                            {menu.key_ingredients?.map((ing: string, i: number) => (
                                <span key={i} className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-md border border-emerald-500/30">{ing}</span>
                            ))}
                        </div>
                    </div>

                    <div className="flex justify-between items-center text-sm">
                        <span className="font-mono text-emerald-400 font-bold">Est. Cost: €{menu.total_estimated_cost}</span>
                    </div>
                    <div className="mt-2 text-xs text-green-200/60 border-t border-white/10 pt-2 flex items-center gap-1">
                        <Lightbulb size={12} /> {menu.savings_note}
                    </div>
                </div>
            )
        }
        if (msg.type === 'recipe' && msg.data) {
            const recipe = msg.data;
            return (
                <div className="bg-white/10 p-4 rounded-xl border border-white/10 mt-2">
                    <h3 className="font-bold text-lg text-amber-300 mb-3 border-b border-white/10 pb-2">Recipe Card</h3>
                    <div className="flex gap-4 text-xs mb-4 text-white/60">
                        <span className="flex items-center gap-1"><Clock size={12} /> {recipe.prep_time} Prep</span>
                        <span className="flex items-center gap-1"><ChefHat size={12} /> {recipe.cooking_time} Cook</span>
                    </div>

                    <div className="mb-4">
                        <h4 className="font-bold text-sm text-white/90 mb-2">Ingredients</h4>
                        <ul className="grid grid-cols-2 gap-1">
                            {recipe.ingredients?.map((ing: string, i: number) => (
                                <li key={i} className="text-sm text-white/70 flex items-center gap-2">
                                    <span className="w-1 h-1 bg-amber-400 rounded-full"></span>
                                    {ing}
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-bold text-sm text-white/90 mb-2">Instructions</h4>
                        <ol className="list-none space-y-2">
                            {recipe.steps?.map((step: string, i: number) => (
                                <li key={i} className="text-sm text-white/70 flex gap-3">
                                    <span className="text-amber-400 font-mono font-bold">{i + 1}.</span>
                                    {step}
                                </li>
                            ))}
                        </ol>
                    </div>
                </div>
            )
        }
        return <p className="text-white/90 leading-relaxed">{msg.content}</p>;
    }

    return (
        <Modal
            isOpen={isOpen}
            onOpenChange={onOpenChange}
            scrollBehavior="inside"
            size="3xl"
            backdrop="blur"
            classNames={{
                base: "bg-[#1e1e24]/90 backdrop-blur-xl border border-white/10 shadow-2xl",
                header: "border-b border-white/10",
                footer: "border-t border-white/10",
                closeButton: "hover:bg-white/10 active:bg-white/20 text-white"
            }}
        >
            <ModalContent className="h-[700px]">
                {(onClose) => (
                    <>
                        <ModalHeader className="flex flex-col gap-1">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-zinc-800 rounded-lg shadow-sm border border-white/10">
                                    <ChefHat className="w-5 h-5 text-white/90" />
                                </div>
                                <div>
                                    <h3 className="text-white font-bold text-lg">AI Budget Chef</h3>
                                    <p className="text-xs font-normal text-white/50">Expert at cooking with discounts</p>
                                </div>
                            </div>
                        </ModalHeader>
                        <ModalBody className="p-0 bg-black/20">
                            <ScrollShadow className="h-full p-6 space-y-6" ref={scrollRef}>
                                {messages.map((msg, idx) => (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        key={idx}
                                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${msg.role === 'user'
                                            ? 'bg-zinc-800 border border-white/10 text-white rounded-tr-sm'
                                            : 'bg-white/5 border border-white/5 backdrop-blur-sm rounded-tl-sm'
                                            }`}>
                                            {renderContent(msg)}
                                        </div>
                                    </motion.div>
                                ))}
                                {isLoading && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="flex justify-start"
                                    >
                                        <div className="bg-white/5 rounded-2xl p-4 rounded-tl-sm flex gap-2 items-center">
                                            <span className="w-2 h-2 bg-white/40 rounded-full animate-bounce"></span>
                                            <span className="w-2 h-2 bg-white/40 rounded-full animate-bounce delay-100"></span>
                                            <span className="w-2 h-2 bg-white/40 rounded-full animate-bounce delay-200"></span>
                                        </div>
                                    </motion.div>
                                )}
                            </ScrollShadow>
                        </ModalBody>
                        <ModalFooter className="p-4">
                            <div className="flex w-full gap-3">
                                <Input
                                    fullWidth
                                    placeholder="Ask for a menu idea..."
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                    classNames={{
                                        inputWrapper: "bg-white/5 border border-white/10 hover:bg-white/10 focus-within:bg-white/10",
                                        input: "text-white placeholder:text-white/30"
                                    }}
                                />
                                <Button
                                    className="bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-white font-bold shadow-sm"
                                    onPress={handleSend}
                                    isLoading={isLoading}
                                    isIconOnly={false}
                                >
                                    Send
                                </Button>
                            </div>
                        </ModalFooter>
                    </>
                )}
            </ModalContent>
        </Modal>
    );
}
