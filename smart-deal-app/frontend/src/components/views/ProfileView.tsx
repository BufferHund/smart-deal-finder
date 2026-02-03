'use client';

import { Card, CardBody, Button, Switch, Avatar, Input, Chip, Divider, Progress } from "@heroui/react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { getUserStats, getUserMemory, updateUserMemory, loadDemoData } from "../../lib/api";
import { Settings, Moon, Sun, User, Utensils, Ban, TrendingUp, Award, Trophy, Database } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function ProfileView() {
    const { theme, setTheme, resolvedTheme } = useTheme();
    const [stats, setStats] = useState<any>(null);
    const [memory, setMemory] = useState<any>({ disliked_items: [], dietary_restrictions: [] });
    const [newItem, setNewItem] = useState("");
    const [newDiet, setNewDiet] = useState("");
    const [isLoadingDemo, setIsLoadingDemo] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [s, m] = await Promise.all([getUserStats(), getUserMemory()]);
            setStats(s);
            setMemory(m);
        } catch (e) {
            console.error(e);
        }
    };

    const handleAddItem = (type: 'dislike' | 'diet') => {
        if (type === 'dislike' && newItem) {
            const updated = { ...memory, disliked_items: [...memory.disliked_items, newItem] };
            setMemory(updated);
            updateUserMemory(updated);
            setNewItem("");
        } else if (type === 'diet' && newDiet) {
            const updated = { ...memory, dietary_restrictions: [...(memory.dietary_restrictions || []), newDiet] };
            setMemory(updated);
            updateUserMemory(updated);
            setNewDiet("");
        }
    };

    const handleRemoveItem = (type: 'dislike' | 'diet', item: string) => {
        if (type === 'dislike') {
            const updated = { ...memory, disliked_items: memory.disliked_items.filter((i: string) => i !== item) };
            setMemory(updated);
            updateUserMemory(updated);
        } else {
            const updated = { ...memory, dietary_restrictions: memory.dietary_restrictions.filter((i: string) => i !== item) };
            setMemory(updated);
            updateUserMemory(updated);
        }
    };

    const level = stats?.gamification?.level || 1;
    const points = stats?.gamification?.points || 0;
    const progress = stats?.gamification?.level_progress || 0;
    const badges = stats?.gamification?.badges || [];

    return (
        <div className="p-4 pb-24 min-h-full space-y-6 text-foreground">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Avatar
                        isBordered
                        color="secondary"
                        src={`https://api.dicebear.com/7.x/notionists/svg?seed=${points}`}
                        className="w-20 h-20 bg-background"
                    />
                    <div>
                        <h1 className="text-3xl font-black text-black dark:text-white">Deal Hunter</h1>
                        <p className="text-pink-500 font-bold text-sm flex items-center gap-1">
                            <Trophy size={14} /> Level {level}
                        </p>
                        <div className="w-32 mt-1">
                            <Progress
                                size="sm"
                                value={progress}
                                color="secondary"
                                aria-label="Level Progress"
                                className="max-w-md"
                            />
                        </div>
                        <p className="text-xs text-black/40 dark:text-white/40 mt-1 font-mono">{points} XP</p>
                    </div>
                </div>
                <Button isIconOnly className="bg-white dark:bg-white/10 shadow-sm" onPress={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </Button>
            </div>

            {/* Badges */}
            {badges.length > 0 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                    {badges.map((badge: string, i: number) => (
                        <Chip key={i} startContent={<Award size={14} />} variant="flat" color="warning" className="text-black dark:text-white bg-yellow-100 dark:bg-yellow-900/30">
                            {badge}
                        </Chip>
                    ))}
                </div>
            )}

            {/* Consumption Chart */}
            <Card className="bg-white dark:bg-[#1c1c1e] border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none">
                <CardBody>
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="font-bold flex items-center gap-2 text-black dark:text-white">
                            <TrendingUp size={18} className="text-pink-500" /> Monthly Spending
                        </h3>
                        <span className="text-2xl font-black text-pink-500">
                            €{stats?.current_month_total?.toFixed(2) || '0.00'}
                        </span>
                    </div>
                    <div className="h-48 w-full">
                        {stats?.chart_data ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={stats.chart_data}>
                                    <XAxis
                                        dataKey="name"
                                        tick={{ fontSize: 10, fill: resolvedTheme === 'dark' ? '#fff' : '#000', opacity: 0.5 }}
                                        stroke="transparent"
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: resolvedTheme === 'dark' ? '#1c1c1e' : '#ffffff',
                                            borderRadius: '12px',
                                            border: 'none',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                            color: resolvedTheme === 'dark' ? '#fff' : '#000'
                                        }}
                                        itemStyle={{ color: resolvedTheme === 'dark' ? '#fff' : '#000' }}
                                        cursor={{ fill: resolvedTheme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
                                    />
                                    <Bar dataKey="value" fill="#ec4899" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-default-300">
                                No data yet
                            </div>
                        )}
                    </div>
                </CardBody>
            </Card>

            {/* Agent Memory */}
            <div className="space-y-4">
                <h3 className="text-xl font-black text-black dark:text-white">Agent Memory 🧠</h3>

                {/* Dislikes */}
                <Card className="bg-white dark:bg-[#1c1c1e] border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none">
                    <CardBody className="space-y-3">
                        <h4 className="font-bold flex items-center gap-2 text-black dark:text-white">
                            <Ban size={16} className="text-red-500" /> Disliked Items
                        </h4>
                        <div className="flex gap-2 flex-wrap">
                            {memory.disliked_items.map((item: string) => (
                                <Chip key={item} onClose={() => handleRemoveItem('dislike', item)} variant="flat" className="bg-red-50 text-red-500 dark:bg-red-500/20 dark:text-red-400">
                                    {item}
                                </Chip>
                            ))}
                        </div>


                        <div className="mb-2">
                            <p className="text-xs text-black/50 dark:text-white/50 mb-2 font-medium">Common Suggestions:</p>
                            <div className="flex gap-2 flex-wrap">
                                {["Cilantro", "Mushrooms", "Olives", "Spicy", "Seafood"].map(s => (
                                    !memory.disliked_items.includes(s) && (
                                        <Chip
                                            key={s}
                                            variant="bordered"
                                            size="sm"
                                            className="cursor-pointer border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/5 transition-colors text-black/60 dark:text-white/60"
                                            onClick={() => {
                                                const updated = { ...memory, disliked_items: [...memory.disliked_items, s] };
                                                setMemory(updated);
                                                updateUserMemory(updated);
                                            }}
                                        >
                                            + {s}
                                        </Chip>
                                    )
                                ))}
                            </div>
                        </div>

                        <div className="flex gap-2">
                            <Input
                                size="sm"
                                placeholder="Add dislike (e.g. Cilantro)"
                                value={newItem}
                                onChange={(e) => setNewItem(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAddItem('dislike')}
                                classNames={{ inputWrapper: "bg-gray-100 dark:bg-white/5" }}
                            />
                            <Button size="sm" onPress={() => handleAddItem('dislike')} className="bg-black text-white dark:bg-white dark:text-black font-bold">Add</Button>
                        </div>
                    </CardBody>
                </Card>

                {/* Dietary */}
                <Card className="bg-white dark:bg-[#1c1c1e] border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none">
                    <CardBody className="space-y-3">
                        <h4 className="font-bold flex items-center gap-2 text-black dark:text-white">
                            <Utensils size={16} className="text-orange-500" /> Dietary Restrictions
                        </h4>
                        <div className="flex gap-2 flex-wrap">
                            {memory.dietary_restrictions?.map((item: string) => (
                                <Chip key={item} onClose={() => handleRemoveItem('diet', item)} variant="flat" className="bg-orange-50 text-orange-500 dark:bg-orange-500/20 dark:text-orange-400">
                                    {item}
                                </Chip>
                            ))}
                        </div>

                        <div className="mb-2">
                            <p className="text-xs text-black/50 dark:text-white/50 mb-2 font-medium">Common Suggestions:</p>
                            <div className="flex gap-2 flex-wrap">
                                {["Vegetarian", "Vegan", "Gluten-Free", "Keto", "Lactose-Free", "Halal"].map(s => (
                                    !memory.dietary_restrictions?.includes(s) && (
                                        <Chip
                                            key={s}
                                            variant="bordered"
                                            size="sm"
                                            className="cursor-pointer border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/5 transition-colors text-black/60 dark:text-white/60"
                                            onClick={() => {
                                                const updated = { ...memory, dietary_restrictions: [...(memory.dietary_restrictions || []), s] };
                                                setMemory(updated);
                                                updateUserMemory(updated);
                                            }}
                                        >
                                            + {s}
                                        </Chip>
                                    )
                                ))}
                            </div>
                        </div>

                        <div className="flex gap-2">
                            <Input
                                size="sm"
                                placeholder="Add diet (e.g. Vegan)"
                                value={newDiet}
                                onChange={(e) => setNewDiet(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAddItem('diet')}
                                classNames={{ inputWrapper: "bg-gray-100 dark:bg-white/5" }}
                            />
                            <Button size="sm" onPress={() => handleAddItem('diet')} className="bg-black text-white dark:bg-white dark:text-black font-bold">Add</Button>
                        </div>
                    </CardBody>
                </Card>
            </div>

            {/* Developer Tools */}
            <Card className="bg-white dark:bg-[#1c1c1e] border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none">
                <CardBody className="space-y-3">
                    <h4 className="font-bold flex items-center gap-2 text-black dark:text-white">
                        <Database size={16} className="text-purple-500" /> Developer Tools
                    </h4>
                    <p className="text-xs text-black/50 dark:text-white/50">Load sample data to test the app with 2000+ German deals.</p>
                    <Button
                        fullWidth
                        className="bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold"
                        isLoading={isLoadingDemo}
                        onPress={async () => {
                            setIsLoadingDemo(true);
                            try {
                                const res = await loadDemoData();
                                alert(res.message || "Demo data loaded!");
                            } catch (e) {
                                alert("Failed to load demo data");
                            } finally {
                                setIsLoadingDemo(false);
                            }
                        }}
                    >
                        Load German Demo Data
                    </Button>
                </CardBody>
            </Card>
        </div>
    );
}
