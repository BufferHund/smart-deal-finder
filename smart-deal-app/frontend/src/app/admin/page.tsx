'use client';

import { useState, useEffect } from 'react';
import {
    Tabs, Tab, Card, CardBody, Button, Progress, Chip, Input, Switch, Select, SelectItem, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure, Spinner
} from "@heroui/react";
import { motion } from 'framer-motion';
import {
    Upload, BarChart3, GitCompare, Settings, FileText, Zap, Clock, Database, CheckCircle, XCircle, Loader2, DollarSign, Users, TrendingUp, BrainCircuit, Bot, Receipt, UserSquare2, Camera, Tags, SlidersHorizontal, Monitor, Trophy, ChartBar, Lightbulb, AlertTriangle, ShoppingCart, Activity, Copy, Trash2, Eye,
    Check,
    X,
    Pencil,
    PenSquare,
    ShoppingBag
} from 'lucide-react';

// API helpers
const API = '/api/admin';

const fetchStats = async () => (await fetch(`${API}/stats`)).json();
const fetchUsage = async (days = 7) => (await fetch(`${API}/usage?days=${days}`)).json();
const fetchQueue = async () => (await fetch(`${API}/queue`)).json();
const fetchBatch = async (id: string) => (await fetch(`${API}/batch/${id}`)).json();
const uploadBatch = async (files: File[], method: string, store: string, ollamaModel?: string) => {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('method', method);
    formData.append('store_name', store);
    if (ollamaModel) formData.append('ollama_model', ollamaModel);
    return (await fetch(`${API}/batch-upload`, { method: 'POST', body: formData })).json();
};
const compareFile = async (file: File, store: string, ollamaModel?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('store_name', store);
    if (ollamaModel) formData.append('ollama_model', ollamaModel);
    return (await fetch(`${API}/compare`, { method: 'POST', body: formData })).json();
};
const compareGeminiModels = async (file: File, store: string, models: string[]) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('store_name', store);
    formData.append('models', models.join(','));
    return (await fetch(`${API}/compare-gemini`, { method: 'POST', body: formData })).json();
    return (await fetch(`${API}/compare-gemini`, { method: 'POST', body: formData })).json();
};
const fetchFeatures = async () => (await fetch(`${API}/features`)).json();
const updateFeatureConfig = async (feature: string, model_id: string) => {
    const formData = new FormData();
    formData.append('feature', feature);
    formData.append('model_id', model_id);
    return (await fetch(`${API}/features/config`, { method: 'POST', body: formData })).json();
};
const testFeature = async (feature: string, file: File, method?: string) => {
    const formData = new FormData();
    formData.append('feature', feature);
    formData.append('file', file);
    if (method) formData.append('method', method);
    return (await fetch(`${API}/features/test`, { method: 'POST', body: formData })).json();
};

// Deals CRUD
const searchDeals = async (query: string, page = 1) => (await fetch(`${API}/deals?q=${query}&page=${page}`)).json();
const createDeal = async (deal: any) => (await fetch(`${API}/deals`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(deal) })).json();
const deleteDeal = async (id: number) => (await fetch(`${API}/deals/${id}`, { method: 'DELETE' })).json();
const deleteDealsBatch = async (ids: number[]) => (await fetch(`${API}/deals/batch-delete`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(ids) })).json();

const runBenchmark = async (feature: string) => {
    const formData = new FormData();
    formData.append('feature', feature);
    return (await fetch(`${API}/features/benchmark`, { method: 'POST', body: formData })).json();
};
const fetchGeminiModels = async () => (await fetch(`${API}/gemini-models`)).json();
const fetchConfig = async () => (await fetch(`${API}/config`)).json();
const fetchLogs = async (limit = 50, offset = 0) => (await fetch(`${API}/audit-log?limit=${limit}&offset=${offset}`)).json();
const fetchLogDetail = async (id: number) => (await fetch(`${API}/audit-log/${id}`)).json();
const fetchUploads = async (limit = 50, offset = 0) => (await fetch(`${API}/uploads?limit=${limit}&offset=${offset}`)).json();
const fetchUploadDeals = async (id: number) => (await fetch(`${API}/uploads/${id}/deals`)).json();
const deleteUpload = async (id: number) => (await fetch(`${API}/uploads/${id}`, { method: 'DELETE' })).json();
const fetchSyntheticCount = async () => (await fetch(`${API}/data/synthetic/count`)).json();
const deleteSyntheticData = async () => (await fetch(`${API}/data/synthetic`, { method: 'DELETE' })).json();
const fetchSyntheticVisibility = async () => (await fetch(`${API}/settings/synthetic-visibility`)).json();
const setSyntheticVisibility = async (show: boolean) => (await fetch(`${API}/settings/synthetic-visibility`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ show })
})).json();

// Cost estimation per method
const COST_PER_PAGE = {
    gemini: 0.01,      // ~$0.01 per page
    local_vlm: 0,       // Free
    ocr_pipeline: 0     // Free
};

export default function AdminPage() {
    const [tab, setTab] = useState('upload');
    const [stats, setStats] = useState<any>(null);
    const [config, setConfig] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const { isOpen, onOpen, onOpenChange } = useDisclosure();
    const [logData, setLogData] = useState<{ input: string, output: string } | null>(null);

    // Audit Logs State
    const [logs, setLogs] = useState<any[]>([]);
    const [logDetail, setLogDetail] = useState<any>(null);
    const { isOpen: isLogOpen, onOpen: onLogOpen, onOpenChange: onLogOpenChange } = useDisclosure();

    // Uploads Data State
    const [uploads, setUploads] = useState<any[]>([]);
    const [selectedUpload, setSelectedUpload] = useState<any>(null);
    const [uploadDeals, setUploadDeals] = useState<any[]>([]);
    const { isOpen: isDealsOpen, onOpen: onDealsOpen, onOpenChange: onDealsOpenChange } = useDisclosure();

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        if (tab === 'logs') loadLogs();
        if (tab === 'data') loadUploads();
    }, [tab]);

    const loadLogs = async () => {
        try {
            const data = await fetchLogs();
            setLogs(data.logs || []);
        } catch (e) { console.error("Failed to load logs", e); }
    };

    const loadUploads = async () => {
        try {
            const data = await fetchUploads();
            setUploads(data.uploads || []);
        } catch (e) { console.error("Failed to load uploads", e); }
    };

    const viewUploadDeals = async (upload: any) => {
        try {
            setSelectedUpload(upload);
            const data = await fetchUploadDeals(upload.id);
            setUploadDeals(data.deals || []);
            onDealsOpen();
        } catch (e) { console.error("Failed to load deals", e); }
    };

    const handleDeleteUpload = async (id: number) => {
        if (confirm("Are you sure you want to delete this upload? This will delete all associated deals.")) {
            await deleteUpload(id);
            loadUploads(); // Refresh list
        }
    };

    const viewLogDetail = async (id: number) => {
        try {
            const detail = await fetchLogDetail(id);
            setLogDetail(detail);
            onLogOpen();
        } catch (e) { console.error("Failed to load log detail", e); }
    };

    const loadData = async () => {
        setLoading(true);
        try {
            const [s, c] = await Promise.all([fetchStats(), fetchConfig()]);
            setStats(s);
            setConfig(c);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    const showLog = (input: string, output: string) => {
        setLogData({ input, output });
        onOpen();
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-slate-900 text-gray-900 dark:text-white">
            {/* Header */}
            <header className="p-6 border-b border-gray-200 dark:border-white/10 bg-white dark:bg-slate-800/50">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-black flex items-center gap-2">
                            <SlidersHorizontal className="w-8 h-8 text-purple-500" /> Admin Manage Panel
                        </h1>
                        <p className="text-gray-500 dark:text-white/50 text-sm">Professional Dashboard for Coursework</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <StatusBadge label="Gemini" active={config?.gemini_configured} />
                        <StatusBadge label="Ollama (VLM)" active={config?.local_vlm_available} />
                        <StatusBadge label="OCR" active={config?.ocr_available} />
                    </div>
                </div>
            </header>

            {/* Tabs */}
            <div className="max-w-7xl mx-auto p-6">
                <Tabs
                    selectedKey={tab}
                    onSelectionChange={(k) => setTab(k as string)}
                    classNames={{
                        tabList: "bg-gray-100 dark:bg-white/5 p-1 rounded-xl",
                        cursor: "bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg",
                        tabContent: "text-gray-600 dark:text-gray-300 group-data-[selected=true]:text-white font-bold"
                    }}
                >
                    <Tab key="intelligence" title={<TabTitle icon={<BrainCircuit size={16} />} text="Model Center" />} />
                    <Tab key="data" title={<TabTitle icon={<Database size={16} />} text="Data Management" />} />
                    <Tab key="logs" title={<TabTitle icon={<FileText size={16} />} text="Audit Logs" />} />
                    <Tab key="upload" title={<TabTitle icon={<Upload size={16} />} text="Batch Upload" />} />
                    <Tab key="analytics" title={<TabTitle icon={<BarChart3 size={16} />} text="Analytics" />} />
                    <Tab key="settings" title={<TabTitle icon={<Settings size={16} />} text="Settings" />} />
                </Tabs>

                <div className="mt-6">
                    {tab === 'intelligence' && <IntelligenceTab showLog={showLog} />}
                    {tab === 'data' && <DataManagementTab uploads={uploads} onViewDeals={viewUploadDeals} onDelete={handleDeleteUpload} onRefresh={loadUploads} />}
                    {tab === 'logs' && <AuditLogsTab logs={logs} onViewDetail={viewLogDetail} onRefresh={loadLogs} />}
                    {tab === 'upload' && <BatchUploadTab onRefresh={loadData} showLog={showLog} />}
                    {tab === 'analytics' && <AnalyticsTab stats={stats} onRefresh={loadData} />}
                    {tab === 'settings' && <SettingsTab config={config} onRefresh={loadData} />}
                </div>
            </div>

            <LogModal isOpen={isOpen} onOpenChange={onOpenChange} logData={logData} />
            <LogDetailModal isOpen={isLogOpen} onOpenChange={onLogOpenChange} log={logDetail} />
            <ViewDealsModal isOpen={isDealsOpen} onClose={() => onDealsOpenChange(false)} upload={selectedUpload} />
        </div>
    );
}

// === Components ===

function TabTitle({ icon, text }: { icon: React.ReactNode; text: string }) {
    return <div className="flex items-center gap-2">{icon} {text}</div>;
}

function StatusBadge({ label, active }: { label: string; active: boolean }) {
    return (
        <div className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 ${active ? 'bg-green-100 text-green-600 dark:bg-green-500/20 dark:text-green-400' : 'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400'}`}>
            {active ? <CheckCircle size={12} /> : <XCircle size={12} />}
            {label}
        </div>
    );
}

function StatCard({ label, value, icon, color = 'purple', subtitle }: { label: string; value: string | number; icon: React.ReactNode; color?: string; subtitle?: string }) {
    const colors: Record<string, string> = {
        purple: 'from-purple-600 to-indigo-600',
        blue: 'from-blue-600 to-cyan-600',
        green: 'from-green-600 to-emerald-600',
        orange: 'from-orange-500 to-amber-500',
        pink: 'from-pink-500 to-rose-500'
    };
    return (
        <Card className={`bg-gradient-to-br ${colors[color]} border-none text-white`}>
            <CardBody className="p-4">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-white/70 text-xs font-medium">{label}</p>
                        <p className="text-3xl font-black mt-1">{value}</p>
                        {subtitle && <p className="text-white/60 text-xs mt-1">{subtitle}</p>}
                    </div>
                    <div className="p-2 bg-white/20 rounded-lg">{icon}</div>
                </div>
            </CardBody>
        </Card>
    );
}

function LogModal({ isOpen, onOpenChange, logData }: { isOpen: boolean; onOpenChange: (isOpen: boolean) => void; logData: { input: string; output: string } | null }) {
    return (
        <Modal isOpen={isOpen} onOpenChange={onOpenChange} size="3xl" scrollBehavior="inside">
            <ModalContent>
                {(onClose) => (
                    <>
                        <ModalHeader className="flex flex-col gap-1">Model Inspection Log</ModalHeader>
                        <ModalBody>
                            <div className="space-y-4">
                                <div>
                                    <h4 className="text-sm font-bold mb-2 flex items-center gap-2 text-purple-600 dark:text-purple-400 font-mono">
                                        📥 Raw Input (Prompt)
                                    </h4>
                                    <pre className="bg-gray-100 dark:bg-slate-800 p-4 rounded text-[10px] text-gray-800 dark:text-slate-200 overflow-auto max-h-48 whitespace-pre-wrap font-mono border border-gray-200 dark:border-white/10">
                                        {logData?.input || 'No input captured'}
                                    </pre>
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold mb-2 flex items-center gap-2 text-green-600 dark:text-green-400 font-mono">
                                        📤 Raw Output (Response)
                                    </h4>
                                    <pre className="bg-gray-100 dark:bg-slate-800 p-4 rounded text-[10px] text-gray-800 dark:text-slate-200 overflow-auto max-h-96 whitespace-pre-wrap font-mono border border-gray-200 dark:border-white/10">
                                        {logData?.output || 'No output captured'}
                                    </pre>
                                </div>
                            </div>
                        </ModalBody>
                        <ModalFooter>
                            <Button color="danger" variant="light" onPress={onClose}>
                                Close
                            </Button>
                        </ModalFooter>
                    </>
                )}
            </ModalContent>
        </Modal>
    );
}

// === Batch Upload Tab ===

function BatchUploadTab({ onRefresh, showLog }: { onRefresh: () => void; showLog: (input: string, output: string) => void }) {
    const [files, setFiles] = useState<File[]>([]);
    const [method, setMethod] = useState('gemini');
    const [store, setStore] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [batchId, setBatchId] = useState<string | null>(null);
    const [batchStatus, setBatchStatus] = useState<any>(null);
    const [config, setConfig] = useState<any>(null);
    const [selectedOllama, setSelectedOllama] = useState<string>('');

    useEffect(() => {
        fetchConfig().then(setConfig);
    }, []);

    const ollamaModels = config?.local_vlm_models || [];

    useEffect(() => {
        if (ollamaModels.length > 0 && !selectedOllama) {
            setSelectedOllama(ollamaModels[0].model_id);
        }
    }, [ollamaModels]);

    const estimatedCost = files.length * (COST_PER_PAGE[method as keyof typeof COST_PER_PAGE] || 0);

    const handleUpload = async () => {
        if (files.length === 0) return;
        setIsUploading(true);
        try {
            const result = await uploadBatch(files, method, store || 'Unknown', method === 'local_vlm' ? selectedOllama : undefined);
            setBatchId(result.batch_id);
            pollBatchStatus(result.batch_id);
        } catch (e) { console.error(e); }
    };

    const pollBatchStatus = async (id: string) => {
        const interval = setInterval(async () => {
            const status = await fetchBatch(id);
            setBatchStatus(status);
            if (status.pending === 0) {
                clearInterval(interval);
                setIsUploading(false);
                onRefresh();
            }
        }, 1000);
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Upload Panel */}
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <Upload size={20} /> Batch Upload
                    </h3>

                    <div
                        className="border-2 border-dashed border-gray-300 dark:border-white/20 rounded-xl p-8 text-center mb-4 hover:border-purple-500/50 transition-colors cursor-pointer bg-gray-50 dark:bg-transparent"
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => {
                            e.preventDefault();
                            setFiles([...files, ...Array.from(e.dataTransfer.files)]);
                        }}
                    >
                        <input
                            type="file"
                            multiple
                            accept=".pdf,.jpg,.jpeg,.png"
                            className="hidden"
                            id="batch-upload"
                            onChange={(e) => setFiles([...files, ...Array.from(e.target.files || [])])}
                        />
                        <label htmlFor="batch-upload" className="cursor-pointer">
                            <FileText size={48} className="mx-auto mb-2 text-gray-500 dark:text-gray-400" />
                            <p className="text-gray-600 dark:text-gray-300">Drop PDFs here or click to select</p>
                            <p className="text-gray-500 dark:text-gray-500 text-sm mt-1">{files.length} files selected</p>
                        </label>
                    </div>

                    {files.length > 0 && (
                        <div className="mb-4 max-h-32 overflow-y-auto">
                            {files.map((f, i) => (
                                <div key={i} className="flex justify-between items-center py-1 text-sm">
                                    <span className="text-gray-700 dark:text-white/70 truncate">{f.name}</span>
                                    <Button size="sm" variant="light" color="danger" onPress={() => setFiles(files.filter((_, j) => j !== i))}>
                                        ✕
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="flex flex-col gap-4 mb-4">
                        <div className="grid grid-cols-2 gap-4">
                            <Select
                                label="Method"
                                selectedKeys={[method]}
                                onSelectionChange={(k) => setMethod([...k][0] as string)}
                                classNames={{ trigger: "bg-gray-100 dark:bg-white/5 border-gray-200 dark:border-white/20" }}
                            >
                                <SelectItem key="gemini">🤖 Gemini API</SelectItem>
                                <SelectItem key="local_vlm"><span className="flex items-center gap-2"><Monitor size={14} /> Local VLM (Ollama)</span></SelectItem>
                                <SelectItem key="ocr_pipeline">📝 OCR Pipeline</SelectItem>
                            </Select>
                            <Input
                                label="Store Name"
                                placeholder="e.g. Aldi"
                                value={store}
                                onChange={(e) => setStore(e.target.value)}
                                classNames={{ inputWrapper: "bg-gray-100 dark:bg-white/5 border-gray-200 dark:border-white/20" }}
                            />
                        </div>

                        {method === 'local_vlm' && (
                            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                                <Select
                                    label="Select Local Model"
                                    selectedKeys={[selectedOllama]}
                                    onSelectionChange={(k) => setSelectedOllama([...k][0] as string)}
                                    placeholder="Choose an installed model"
                                    classNames={{ trigger: "bg-purple-100/50 dark:bg-purple-500/10 border-purple-200 dark:border-purple-500/30" }}
                                >
                                    {ollamaModels.map((m: any) => (
                                        <SelectItem key={m.model_id} textValue={m.model_id}>
                                            <div className="flex justify-between items-center w-full">
                                                <span>{m.model_id}</span>
                                                <span className="text-[10px] opacity-50">{m.size}</span>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </Select>
                            </motion.div>
                        )}
                    </div>

                    {/* Cost Estimation */}
                    <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-500/10 rounded-lg border border-blue-200 dark:border-blue-500/30">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-blue-700 dark:text-blue-300 flex items-center gap-1"><DollarSign size={14} /> Estimated Cost:</span>
                            <span className="font-bold text-blue-800 dark:text-blue-200">
                                {estimatedCost > 0 ? `$${estimatedCost.toFixed(2)}` : 'Free'}
                            </span>
                        </div>
                    </div>

                    <Button
                        color="secondary"
                        className="w-full font-bold"
                        size="lg"
                        isLoading={isUploading}
                        onPress={handleUpload}
                        isDisabled={files.length === 0}
                    >
                        Process {files.length} Files
                    </Button>
                </CardBody>
            </Card>

            {/* Queue Status */}
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <Loader2 size={20} className={batchStatus?.pending > 0 ? 'animate-spin' : ''} /> Processing Queue
                    </h3>

                    {batchStatus ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-3 gap-4 text-center">
                                <div className="bg-yellow-50 dark:bg-yellow-500/10 p-3 rounded-lg">
                                    <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{batchStatus.pending}</p>
                                    <p className="text-xs text-yellow-700 dark:text-yellow-300">Pending</p>
                                </div>
                                <div className="bg-green-50 dark:bg-green-500/10 p-3 rounded-lg">
                                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">{batchStatus.completed}</p>
                                    <p className="text-xs text-green-700 dark:text-green-300">Completed</p>
                                </div>
                                <div className="bg-red-50 dark:bg-red-500/10 p-3 rounded-lg">
                                    <p className="text-2xl font-bold text-red-600 dark:text-red-400">{batchStatus.failed}</p>
                                    <p className="text-xs text-red-700 dark:text-red-300">Failed</p>
                                </div>
                            </div>

                            <Progress
                                value={(batchStatus.completed / batchStatus.total) * 100}
                                classNames={{ indicator: "bg-gradient-to-r from-purple-500 to-pink-500" }}
                            />

                            <div className="max-h-64 overflow-y-auto space-y-2">
                                {batchStatus.jobs?.map((job: any) => (
                                    <div key={job.id} className="flex justify-between items-center text-sm p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-transparent hover:border-purple-500/30 transition-colors">
                                        <div className="flex flex-col flex-1 min-w-0 mr-4">
                                            <span className="truncate text-gray-700 dark:text-white font-medium">{job.file_name}</span>
                                            {job.status === 'failed' && job.result?.error && (
                                                <span className="text-xs text-red-500 truncate" title={job.result.error}>
                                                    {job.result.error}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {(job.status === 'completed' || job.status === 'failed') && (job.result?.raw_input || job.result?.raw_response) && (
                                                <Button
                                                    size="sm"
                                                    variant="flat"
                                                    color="secondary"
                                                    isIconOnly
                                                    onPress={() => showLog(job.result.raw_input || "", job.result.raw_response || "")}
                                                >
                                                    <FileText size={14} />
                                                </Button>
                                            )}
                                            <StatusChip status={job.status} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                            <Loader2 size={32} className="mx-auto mb-2" />
                            <p>No active batch</p>
                        </div>
                    )}
                </CardBody>
            </Card>
        </div>
    );
}

// === Intelligence Center Tab ===

function IntelligenceTab({ showLog }: { showLog: (input: string, output: string) => void }) {
    const [features, setFeatures] = useState<any>(null);
    const [geminiModels, setGeminiModels] = useState<string[]>([]);
    const [localModels, setLocalModels] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [featData, geminiData, configData] = await Promise.all([
                fetchFeatures(),
                fetchGeminiModels(),
                fetchConfig()
            ]);
            setFeatures(featData.features);
            setGeminiModels(geminiData.models || []);
            setLocalModels(configData.local_vlm_models || []);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    if (loading) return <div className="text-center py-12"><Loader2 className="animate-spin mx-auto" /></div>;

    return (
        <div className="space-y-6">
            <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl p-8 text-white shadow-lg">
                <h2 className="text-3xl font-black mb-2 flex items-center gap-3">
                    <BrainCircuit size={32} /> Model Center
                </h2>
                <p className="opacity-90 max-w-2xl">
                    Configure specialized AI models for each application feature. Run benchmarks directly to verify performance.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {features && Object.entries(features).map(([key, config]: [string, any]) => (
                    <FeatureCard
                        key={key}
                        featureKey={key}
                        config={config}
                        geminiModels={geminiModels}
                        localModels={localModels}
                        onUpdate={loadData}
                        showLog={showLog}
                    />
                ))}
            </div>
        </div>
    );
}

function FeatureCard({
    featureKey,
    config,
    geminiModels = [],
    localModels = [],
    onUpdate,
    showLog
}: {
    featureKey: string,
    config: any,
    geminiModels?: string[],
    localModels?: any[],
    onUpdate: () => void,
    showLog: (i: string, o: string) => void
}) {
    const [isBenchmarkRunning, setIsBenchmarkRunning] = useState(false);
    const [isTesting, setIsTesting] = useState(false);
    const [testFile, setTestFile] = useState<File | null>(null);
    const [testResult, setTestResult] = useState<any>(null);

    // Safety: Ensure config exists
    const safeConfig = config || { default_model: 'gemini-2.5-flash', name: 'Unknown', description: '', allowed_models: [] };
    const defaultModel = safeConfig.default_model || 'gemini-2.5-flash';

    // Initial method state based on default model
    const [method, setMethod] = useState<string>(() => {
        if (defaultModel.includes('gemini')) return 'gemini';
        if (defaultModel.includes('ocr')) return 'ocr_pipeline';
        return 'local_vlm';
    });

    // Sync method if config changes externally (e.g. after update)
    useEffect(() => {
        if (defaultModel.includes('gemini') && method !== 'gemini') setMethod('gemini');
        else if (defaultModel.includes('ocr') && method !== 'ocr_pipeline') setMethod('ocr_pipeline');
        // For Local VLM we don't auto-switch as strictly to avoid jumping around
    }, [defaultModel]);

    const icons: Record<string, any> = {
        discount_brochure: Tags,
        shopping_agent: Bot,
        invoice_parser: Receipt,
        member_card: UserSquare2,
        chef_photo: Camera
    };
    const Icon = icons[featureKey] || BrainCircuit;

    const handleModelChange = async (model: string) => {
        await updateFeatureConfig(featureKey, model);
        onUpdate();
    };

    const handleBenchmark = async () => {
        setIsBenchmarkRunning(true);
        await runBenchmark(featureKey);
        setTimeout(() => setIsBenchmarkRunning(false), 2000); // Mock feedback
    };

    const handleTest = async () => {
        if (!testFile) return;
        setIsTesting(true);
        try {
            const res = await testFeature(featureKey, testFile, method);
            setTestResult(res);
            if (res.raw_response) showLog(res.raw_input || "N/A", res.raw_response);
        } catch (e) {
            console.error(e);
        }
        setIsTesting(false);
    };

    // Determine available models based on method
    const getAvailableModels = () => {
        // Fix: geminiModels provides objects, we need to extract model_id
        if (method === 'gemini') return Array.isArray(geminiModels) ? geminiModels.map((m: any) => typeof m === 'string' ? m : m.model_id) : [];
        if (method === 'local_vlm') return Array.isArray(localModels) ? localModels.map((m: any) => m.model_id) : [];
        if (method === 'ocr_pipeline') return ['ocr-default'];
        return [];
    };

    // Auto-select first model if current config is invalid for method
    useEffect(() => {
        const available = getAvailableModels();
        if (method === 'ocr_pipeline') return; // No model selection for pipeline

        // Check if current default model is in the available list for this method
        const isCurrentValid = available.includes(defaultModel);

        // Logic: Should we auto-switch? 
        // Only if the user explicitly changed method and the current model is definitely wrong type.
        // Simple heuristic: If method is gemini but model is not gemini...
        if (method === 'gemini' && !defaultModel.includes('gemini') && available.length > 0) {
            // handleModelChange(available[0]); // Be careful with auto-save
        }
    }, [method, geminiModels, localModels]);

    const modelOptions = getAvailableModels();

    // Safety check for current default model
    const isCloud = defaultModel.includes('gemini');

    return (
        <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 overflow-visible">
            <CardBody className="p-6">
                <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-indigo-50 dark:bg-indigo-500/20 rounded-xl text-indigo-600 dark:text-indigo-300">
                        <Icon size={24} />
                    </div>
                    {/* Dynamic Status Chip based on selected Method */}
                    {method === 'gemini' && (
                        <Chip size="sm" color="secondary" variant="flat" startContent={<Zap size={12} />}>Online VLM</Chip>
                    )}
                    {method === 'local_vlm' && (
                        <Chip size="sm" color="success" variant="flat" startContent={<Database size={12} />}>Local VLM</Chip>
                    )}
                    {method === 'ocr_pipeline' && (
                        <Chip size="sm" color="warning" variant="flat" startContent={<FileText size={12} />}>Pipeline</Chip>
                    )}
                </div>

                <h3 className="text-xl font-bold mb-1">{safeConfig.name}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 min-h-[40px]">{safeConfig.description}</p>

                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Method</label>
                            <Select
                                size="sm"
                                selectedKeys={[method]}
                                onSelectionChange={(s) => setMethod([...s][0] as string)}
                                className="w-full"
                            >
                                <SelectItem key="gemini">Online VLM</SelectItem>
                                <SelectItem key="local_vlm">Local VLM</SelectItem>
                                <SelectItem key="ocr_pipeline">Pipeline</SelectItem>
                            </Select>
                        </div>
                        <div>
                            <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Model</label>
                            <Select
                                size="sm"
                                selectedKeys={method === 'ocr_pipeline' ? [] : [defaultModel]}
                                onSelectionChange={(s) => handleModelChange([...s][0] as string)}
                                className="w-full"
                                isDisabled={method === 'ocr_pipeline'}
                                placeholder={method === 'ocr_pipeline' ? 'N/A' : 'Select Model'}
                            >
                                {modelOptions.map((m: string) => (
                                    <SelectItem key={m} textValue={m}>{m}</SelectItem>
                                ))}
                            </Select>
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <div className="flex-1">
                            <input type="file" id={`file-${featureKey}`} className="hidden" onChange={e => setTestFile(e.target.files?.[0] || null)} />
                            <label htmlFor={`file-${featureKey}`} className={`block text-center text-xs py-2 border border-dashed rounded cursor-pointer ${testFile ? 'border-purple-500 text-purple-600 bg-purple-50' : 'border-gray-300 text-gray-400'}`}>
                                {testFile ? 'File Selected' : 'Upload Test File'}
                            </label>
                        </div>
                        <Button size="sm" isIconOnly color="secondary" onPress={handleTest} isLoading={isTesting} isDisabled={!testFile}>
                            <Zap size={16} />
                        </Button>
                    </div>

                    <div className="pt-4 border-t border-gray-100 dark:border-white/10 flex justify-between items-center">
                        {false && (
                            <Button
                                font-size="xs"
                                variant="light"
                                color={isBenchmarkRunning ? "success" : "default"}
                                startContent={isBenchmarkRunning ? <Loader2 size={14} className="animate-spin" /> : <BarChart3 size={14} />}
                                onPress={handleBenchmark}
                            >
                                {isBenchmarkRunning ? "Running..." : "Run Benchmark"}
                            </Button>
                        )}
                        <span className="text-[10px] text-gray-400 font-mono">v1.2</span>
                    </div>
                </div>
            </CardBody>
        </Card>
    );
}

function StatusChip({ status }: { status: string }) {
    const colors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400',
        processing: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',
        completed: 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400',
        failed: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
    };
    return <span className={`px-2 py-1 rounded-full text-xs font-bold ${colors[status]}`}>{status}</span>;
}

// === Analytics Tab ===

function AnalyticsTab({ stats, onRefresh }: { stats: any; onRefresh: () => void }) {
    if (!stats) return <div className="text-center py-12 text-gray-400 dark:text-white/40">Loading...</div>;

    const methods = stats.usage?.by_method || {};

    // Calculate total cost
    let totalCost = 0;
    Object.entries(methods).forEach(([method, data]: [string, any]) => {
        totalCost += (data.count || 0) * (COST_PER_PAGE[method as keyof typeof COST_PER_PAGE] || 0);
    });

    return (
        <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <StatCard label="Total Deals" value={stats.total_deals} icon={<Database size={20} />} color="purple" />
                <StatCard label="Stores" value={Object.keys(stats.stores || {}).length} icon={<FileText size={20} />} color="blue" />
                <StatCard label="Weekly Extractions" value={stats.weekly_extractions} icon={<Zap size={20} />} color="green" />
                <StatCard label="Avg Duration" value={`${stats.usage?.avg_duration_ms || 0}ms`} icon={<Clock size={20} />} color="orange" />
                <StatCard label="Est. Cost" value={`$${totalCost.toFixed(2)}`} icon={<DollarSign size={20} />} color="pink" subtitle="This week" />
            </div>

            {/* Method Usage with Cost */}
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><ChartBar size={18} /> Method Usage & Cost (Last 7 Days)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {['gemini', 'local_vlm', 'ocr_pipeline'].map(method => {
                            const data = methods[method] || { count: 0, deals: 0, avg_duration_ms: 0, success_rate: 0 };
                            const cost = data.count * (COST_PER_PAGE[method as keyof typeof COST_PER_PAGE] || 0);
                            const methodNames: Record<string, { name: string; icon: string | null }> = {
                                gemini: { name: 'Gemini API', icon: '🤖' },
                                local_vlm: { name: 'Local VLM', icon: null },
                                ocr_pipeline: { name: 'OCR Pipeline', icon: '📝' }
                            };

                            return (
                                <div key={method} className="bg-gray-50 dark:bg-white/5 p-4 rounded-xl border border-gray-100 dark:border-white/10">
                                    <div className="flex justify-between items-center mb-3">
                                        <span className="font-bold">{methodNames[method].icon} {methodNames[method].name}</span>
                                        <Chip size="sm" color="secondary">{data.count} runs</Chip>
                                    </div>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between text-gray-600 dark:text-white/70">
                                            <span>Deals extracted:</span>
                                            <span className="font-bold text-gray-900 dark:text-white">{data.deals}</span>
                                        </div>
                                        <div className="flex justify-between text-gray-600 dark:text-white/70">
                                            <span>Avg duration:</span>
                                            <span>{data.avg_duration_ms}ms</span>
                                        </div>
                                        <div className="flex justify-between text-gray-600 dark:text-white/70">
                                            <span>Success rate:</span>
                                            <span className="text-green-600 dark:text-green-400">{(data.success_rate || 0).toFixed(1)}%</span>
                                        </div>
                                        <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-white/10">
                                            <span className="text-gray-600 dark:text-white/70">Cost:</span>
                                            <span className="font-bold text-purple-600 dark:text-purple-400">
                                                {cost > 0 ? `$${cost.toFixed(2)}` : 'Free'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </CardBody>
            </Card>

            {/* Store Distribution */}
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="text-lg font-bold mb-4 text-gray-900 dark:text-white">🏪 Store Distribution</h3>
                    {Object.keys(stats.stores || {}).length === 0 ? (
                        <p className="text-gray-400 dark:text-white/40 text-center py-4">No stores yet. Upload some flyers!</p>
                    ) : (
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(stats.stores || {}).map(([store, count]) => (
                                <Chip key={store} variant="flat" color="secondary" size="lg">
                                    {store}: {count as number}
                                </Chip>
                            ))}
                        </div>
                    )}
                </CardBody>
            </Card>

            {/* Category Distribution */}
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="text-lg font-bold mb-4 text-gray-900 dark:text-white">📦 Category Distribution</h3>
                    {Object.keys(stats.categories || {}).length === 0 ? (
                        <p className="text-gray-400 dark:text-white/40 text-center py-4">No categories yet.</p>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {Object.entries(stats.categories || {}).map(([cat, count]) => (
                                <div key={cat} className="bg-gray-50 dark:bg-white/5 p-3 rounded-lg text-center">
                                    <p className="font-bold text-lg">{count as number}</p>
                                    <p className="text-xs text-gray-500 dark:text-white/50">{cat}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </CardBody>
            </Card>
        </div>
    );
}

// === Compare Methods Tab ===

function CompareTab({ showLog }: { showLog: (input: string, output: string) => void }) {
    const [file, setFile] = useState<File | null>(null);
    const [store, setStore] = useState('Test Store');
    const [isComparing, setIsComparing] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [config, setConfig] = useState<any>(null);
    const [selectedOllama, setSelectedOllama] = useState<string>('');

    useEffect(() => {
        fetchConfig().then(cfg => {
            setConfig(cfg);
            if (cfg?.local_vlm_models?.length > 0) {
                setSelectedOllama(cfg.local_vlm_models[0].model_id);
            }
        });
    }, []);

    const handleCompare = async () => {
        if (!file) return;
        setIsComparing(true);
        try {
            const res = await compareFile(file, store, selectedOllama);
            setResult(res);
        } catch (e) { console.error(e); }
        setIsComparing(false);
    };

    return (
        <div className="space-y-6">
            {/* Upload for comparison */}
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <GitCompare size={20} /> Method Comparison
                    </h3>
                    <p className="text-gray-600 dark:text-white/60 text-sm mb-4">
                        Upload a single PDF to compare all three extraction methods side-by-side. Perfect for coursework evaluation.
                    </p>

                    <div className="flex gap-4 items-end flex-wrap">
                        <div className="flex-1 min-w-[200px]">
                            <input
                                type="file"
                                accept=".pdf,.jpg,.jpeg,.png"
                                className="hidden"
                                id="compare-upload"
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                            />
                            <label htmlFor="compare-upload" className="block">
                                <div className="p-4 border border-dashed border-gray-300 dark:border-white/20 rounded-lg text-center cursor-pointer hover:border-purple-500/50 bg-gray-50 dark:bg-transparent">
                                    {file ? file.name : 'Click to select file'}
                                </div>
                            </label>
                        </div>
                        <Input
                            label="Store"
                            value={store}
                            onChange={(e) => setStore(e.target.value)}
                            className="w-40"
                            classNames={{ inputWrapper: "bg-gray-100 dark:bg-white/5 border-gray-200 dark:border-white/20" }}
                        />
                        <Button
                            color="secondary"
                            size="lg"
                            isLoading={isComparing}
                            onPress={handleCompare}
                            isDisabled={!file}
                        >
                            Compare All
                        </Button>
                    </div>

                    {config?.local_vlm_models?.length > 0 && (
                        <div className="mt-4 flex items-center gap-3">
                            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Ollama Model:</span>
                            <Select
                                size="sm"
                                variant="bordered"
                                selectedKeys={[selectedOllama]}
                                onSelectionChange={(k) => setSelectedOllama([...k][0] as string)}
                                className="max-w-[200px]"
                                classNames={{ trigger: "border-purple-200 dark:border-purple-500/30 h-8 min-h-unit-8" }}
                            >
                                {config.local_vlm_models.map((m: any) => (
                                    <SelectItem key={m.model_id} textValue={m.model_id}>
                                        {m.model_id}
                                    </SelectItem>
                                ))}
                            </Select>
                            <p className="text-[10px] text-gray-400">Chosen model will be used for the Local VLM comparison run.</p>
                        </div>
                    )}
                </CardBody>
            </Card>

            {/* Results */}
            {result && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                        <CardBody className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-bold">📋 Comparison Results</h3>
                                {result.winner && (
                                    <Chip color="success" variant="flat">
                                        <Trophy className="inline w-4 h-4 mr-1" /> Winner: {result.winner.method}
                                    </Chip>
                                )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {Object.entries(result.results || {}).map(([method, data]: [string, any]) => (
                                    <div
                                        key={method}
                                        className={`p-4 rounded-xl border ${data.success ? 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/10' : 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/30'} ${result.winner?.method === method ? 'ring-2 ring-green-500' : ''}`}
                                    >
                                        <div className="flex justify-between items-center mb-3">
                                            <h4 className="font-bold capitalize">{method.replace('_', ' ')}</h4>
                                            <div className="flex items-center gap-2">
                                                {data.success && (
                                                    <Button
                                                        size="sm"
                                                        variant="flat"
                                                        isIconOnly
                                                        onPress={() => showLog(data.raw_input || "", data.raw_response || "")}
                                                    >
                                                        <FileText size={14} />
                                                    </Button>
                                                )}
                                                {data.success ? (
                                                    <CheckCircle size={20} className="text-green-500" />
                                                ) : (
                                                    <XCircle size={20} className="text-red-500" />
                                                )}
                                            </div>
                                        </div>

                                        {data.success ? (
                                            <div className="space-y-2 text-sm">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-500 dark:text-white/60">Deals found:</span>
                                                    <span className="font-bold text-lg">{data.deal_count}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-500 dark:text-white/60">Duration:</span>
                                                    <span>{data.duration_ms}ms</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-500 dark:text-white/60">Est. Cost:</span>
                                                    <span className="text-purple-600 dark:text-purple-400">
                                                        {method === 'gemini' ? '$0.01' : 'Free'}
                                                    </span>
                                                </div>
                                                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-white/10">
                                                    <p className="text-xs text-gray-400 dark:text-white/50 mb-1">Sample deals:</p>
                                                    {data.deals?.slice(0, 3).map((d: any, i: number) => (
                                                        <p key={i} className="text-xs truncate">• {d.product_name}</p>
                                                    ))}
                                                </div>
                                            </div>
                                        ) : (
                                            <p className="text-red-600 dark:text-red-400 text-sm">{data.error}</p>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* Comparison Table for Coursework */}
                            <div className="mt-6 overflow-x-auto">
                                <h4 className="font-bold mb-3 flex items-center gap-2"><ChartBar size={16} /> Summary Table (Export for Coursework)</h4>
                                <table className="w-full text-sm border border-gray-200 dark:border-white/10 rounded-lg overflow-hidden">
                                    <thead className="bg-gray-100 dark:bg-white/5">
                                        <tr>
                                            <th className="text-left py-3 px-4 font-bold">Metric</th>
                                            <th className="text-center py-3 px-4 font-bold">🤖 Gemini API</th>
                                            <th className="text-center py-3 px-4 font-bold"><Monitor className="inline w-4 h-4 mr-1" /> Local VLM</th>
                                            <th className="text-center py-3 px-4 font-bold">📝 OCR Pipeline</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="border-t border-gray-200 dark:border-white/5">
                                            <td className="py-3 px-4 text-gray-600 dark:text-white/60">Deals Extracted</td>
                                            <td className="text-center font-bold">{result.results?.gemini?.deal_count ?? '-'}</td>
                                            <td className="text-center font-bold">{result.results?.local_vlm?.deal_count ?? '-'}</td>
                                            <td className="text-center font-bold">{result.results?.ocr_pipeline?.deal_count ?? '-'}</td>
                                        </tr>
                                        <tr className="border-t border-gray-200 dark:border-white/5">
                                            <td className="py-3 px-4 text-gray-600 dark:text-white/60">Duration (ms)</td>
                                            <td className="text-center">{result.results?.gemini?.duration_ms ?? '-'}</td>
                                            <td className="text-center">{result.results?.local_vlm?.duration_ms ?? '-'}</td>
                                            <td className="text-center">{result.results?.ocr_pipeline?.duration_ms ?? '-'}</td>
                                        </tr>
                                        <tr className="border-t border-gray-200 dark:border-white/5">
                                            <td className="py-3 px-4 text-gray-600 dark:text-white/60">Cost per Page</td>
                                            <td className="text-center">$0.01</td>
                                            <td className="text-center">Free</td>
                                            <td className="text-center">Free</td>
                                        </tr>
                                        <tr className="border-t border-gray-200 dark:border-white/5">
                                            <td className="py-3 px-4 text-gray-600 dark:text-white/60">Status</td>
                                            <td className="text-center">{result.results?.gemini?.success ? '✅ Success' : '❌ Failed'}</td>
                                            <td className="text-center">{result.results?.local_vlm?.success ? '✅ Success' : '❌ Failed'}</td>
                                            <td className="text-center">{result.results?.ocr_pipeline?.success ? '✅ Success' : '❌ Failed'}</td>
                                        </tr>
                                        <tr className="border-t border-gray-200 dark:border-white/5 bg-purple-50 dark:bg-purple-500/10">
                                            <td className="py-3 px-4 font-bold">Expected Accuracy</td>
                                            <td className="text-center font-bold text-purple-600 dark:text-purple-400">~95%</td>
                                            <td className="text-center font-bold text-purple-600 dark:text-purple-400">~85%</td>
                                            <td className="text-center font-bold text-purple-600 dark:text-purple-400">~70%</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </CardBody>
                    </Card>
                </motion.div>
            )}
        </div>
    );
}

// === Settings Tab ===

function SettingsTab({ config, onRefresh }: { config: any; onRefresh: () => void }) {
    const [models, setModels] = useState<any[]>([]);

    useEffect(() => {
        fetchGeminiModels().then(data => setModels(data.models || []));
    }, []);

    return (
        <div className="max-w-2xl mx-auto space-y-4">
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="font-bold mb-4 text-lg text-gray-900 dark:text-white">🔧 Extraction Methods & Real Costs</h3>
                    <div className="space-y-4">
                        <div className="p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/10">
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <p className="font-bold text-gray-900 dark:text-white">⚡ Online VLM (Gemini)</p>
                                    <p className="text-xs text-gray-500 dark:text-white/50">Cloud-based multimodal LLM. Pricing based on input tokens (images + text).</p>
                                </div>
                                <StatusBadge label={config?.gemini_configured ? 'Active' : 'Not Set'} active={config?.gemini_configured} />
                            </div>

                            {/* Dynamic Pricing Table */}
                            <div className="mt-3 bg-white dark:bg-black/20 rounded border border-gray-100 dark:border-white/10 overflow-hidden">
                                <table className="w-full text-xs">
                                    <thead className="bg-gray-50 dark:bg-white/5">
                                        <tr>
                                            <th className="p-2 text-left">Model Name</th>
                                            <th className="p-2 text-right">Cost / 1K Tokens</th>
                                            <th className="p-2 text-right">~Cost / Page</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 dark:divide-white/5">
                                        {models.length > 0 ? models.map(m => (
                                            <tr key={m.model_id}>
                                                <td className="p-2 font-medium">{m.display_name} <span className="text-[10px] text-gray-400">({m.model_id})</span></td>
                                                <td className="p-2 text-right font-mono">${(m.cost_per_1k_tokens * 1000).toFixed(4)}</td>
                                                <td className="p-2 text-right font-mono text-purple-600 dark:text-purple-400">
                                                    ${(m.cost_per_1k_tokens * 1000 * 2).toFixed(4)} <span className="text-[10px] opacity-50">(est)</span>
                                                </td>
                                            </tr>
                                        )) : (
                                            <tr><td colSpan={3} className="p-2 text-center opacity-50">Loading pricing...</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/10">
                            <div>
                                <p className="font-bold flex items-center gap-2 text-gray-900 dark:text-white"><Monitor size={16} /> 🖥️ Local VLM (Ollama)</p>
                                <p className="text-xs text-gray-500 dark:text-white/50">Ollama + LLaVA, runs locally, privacy-first</p>
                                <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-bold">Cost: $0.00 (Free)</p>
                            </div>
                            <StatusBadge label="Setup Required" active={false} />
                        </div>
                        <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/10">
                            <div>
                                <p className="font-bold text-gray-900 dark:text-white">📝 Pipeline (OCR)</p>
                                <p className="text-xs text-gray-500 dark:text-white/50">Tesseract OCR + regex parsing, fastest method</p>
                                <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-bold">Cost: $0.00 (Free)</p>
                            </div>
                            <StatusBadge label={config?.ocr_available ? 'Ready' : 'Not Found'} active={config?.ocr_available} />
                        </div>
                    </div>
                </CardBody>
            </Card>

            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="font-bold mb-4 text-lg text-gray-900 dark:text-white">📚 Method Comparison Guide (For Coursework)</h3>
                    <div className="space-y-4 text-sm">
                        <div className="p-4 bg-blue-50 dark:bg-blue-500/10 rounded-lg border border-blue-200 dark:border-blue-500/20">
                            <h4 className="font-bold text-blue-800 dark:text-blue-300 mb-2">🤖 Gemini API (Multimodal LLM)</h4>
                            <p className="text-blue-700 dark:text-blue-200">Uses Google's Gemini 2.0 Flash to understand images directly. The model can "see" the flyer and extract structured data. Best for complex layouts, handwritten prices, and promotional text.</p>
                            <p className="text-blue-600 dark:text-blue-300 mt-2"><b>Pros:</b> Highest accuracy (~95%), handles complex layouts</p>
                            <p className="text-blue-600 dark:text-blue-300"><b>Cons:</b> Costs money, requires internet, data leaves your machine</p>
                        </div>

                        <div className="p-4 bg-green-50 dark:bg-green-500/10 rounded-lg border border-green-200 dark:border-green-500/20">
                            <h4 className="font-bold text-green-800 dark:text-green-300 mb-2 flex items-center gap-2"><Monitor size={16} /> Local VLM (LLaVA via Ollama)</h4>
                            <p className="text-green-700 dark:text-green-200">Runs a vision-language model locally using Ollama. Similar concept to Gemini but everything stays on your machine. LLaVA is trained to understand images and answer questions.</p>
                            <p className="text-green-600 dark:text-green-300 mt-2"><b>Pros:</b> Free, private, works offline</p>
                            <p className="text-green-600 dark:text-green-300"><b>Cons:</b> Requires GPU (8GB+ VRAM), slightly less accurate (~85%)</p>
                        </div>

                        <div className="p-4 bg-orange-50 dark:bg-orange-500/10 rounded-lg border border-orange-200 dark:border-orange-500/20">
                            <h4 className="font-bold text-orange-800 dark:text-orange-300 mb-2">📝 OCR Pipeline (Tesseract + Regex)</h4>
                            <p className="text-orange-700 dark:text-orange-200">Traditional approach: 1) Convert PDF to images 2) Run Tesseract OCR to extract text 3) Use regex patterns to find prices (e.g., /\\d+[,.]\\d{2}€/). No AI understanding, pure pattern matching.</p>
                            <p className="text-orange-600 dark:text-orange-300 mt-2"><b>Pros:</b> Fastest, free, works anywhere, deterministic</p>
                            <p className="text-orange-600 dark:text-orange-300"><b>Cons:</b> Lowest accuracy (~70%), struggles with complex layouts</p>
                        </div>
                    </div>
                </CardBody>
            </Card>
        </div>
    );
}

// === Gemini Models Comparison Tab ===

function GeminiCompareTab({ showLog }: { showLog: (input: string, output: string) => void }) {
    const [file, setFile] = useState<File | null>(null);
    const [store, setStore] = useState('Test Store');
    const [isComparing, setIsComparing] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [models, setModels] = useState<any[]>([]);
    const [selectedModels, setSelectedModels] = useState<string[]>([
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-3-flash-preview'
    ]);

    useEffect(() => {
        loadModels();
    }, []);

    const loadModels = async () => {
        try {
            const data = await fetchGeminiModels();
            if (data.models) setModels(data.models);
        } catch (e) { console.error(e); }
    };

    const toggleModel = (modelId: string) => {
        if (selectedModels.includes(modelId)) {
            setSelectedModels(selectedModels.filter(m => m !== modelId));
        } else {
            setSelectedModels([...selectedModels, modelId]);
        }
    };

    const handleCompare = async () => {
        if (!file || selectedModels.length === 0) {
            console.log('Missing file or models:', { file, selectedModels });
            return;
        }
        console.log('Starting comparison with:', { file: file.name, store, models: selectedModels });
        setIsComparing(true);
        setResult(null);  // Clear previous results
        try {
            const res = await compareGeminiModels(file, store, selectedModels);
            console.log('Comparison result:', res);
            setResult(res);
        } catch (e) {
            console.error('Comparison error:', e);
            setResult({ error: String(e), success: false });
        }
        setIsComparing(false);
    };

    return (
        <div className="space-y-6">
            {/* Model Selection & Upload */}
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white">
                <CardBody className="p-6">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <Zap size={20} /> Compare Gemini Models
                    </h3>
                    <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
                        Test the same flyer across multiple Gemini model variants to compare accuracy and cost.
                    </p>

                    {/* Model Selection */}
                    <div className="mb-4">
                        <p className="text-sm font-bold mb-2">Select Models to Compare:</p>
                        <div className="flex flex-wrap gap-2">
                            {models.map((m: any) => (
                                <button
                                    key={m.model_id}
                                    onClick={() => toggleModel(m.model_id)}
                                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${selectedModels.includes(m.model_id)
                                        ? 'bg-purple-500 text-white'
                                        : 'bg-gray-100 dark:bg-white/5 text-gray-700 dark:text-white/70 hover:bg-gray-200 dark:hover:bg-white/10'
                                        }`}
                                >
                                    {m.display_name}
                                    <span className="ml-2 text-xs opacity-70">
                                        ${(m.cost_per_1k_tokens * 1000).toFixed(4)}/1K
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* File Upload */}
                    <div className="flex gap-4 items-end flex-wrap">
                        <div className="flex-1 min-w-[200px]">
                            <input
                                type="file"
                                accept=".pdf,.jpg,.jpeg,.png"
                                className="hidden"
                                id="gemini-compare-upload"
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                            />
                            <label htmlFor="gemini-compare-upload" className="block">
                                <div className="p-4 border border-dashed border-gray-300 dark:border-white/20 rounded-lg text-center cursor-pointer hover:border-purple-500/50 bg-gray-50 dark:bg-transparent">
                                    {file ? file.name : 'Click to select flyer image/PDF'}
                                </div>
                            </label>
                        </div>
                        <Input
                            label="Store"
                            value={store}
                            onChange={(e) => setStore(e.target.value)}
                            className="w-40"
                            classNames={{ inputWrapper: "bg-gray-100 dark:bg-white/5 border-gray-200 dark:border-white/20" }}
                        />
                        <Button
                            color="secondary"
                            size="lg"
                            isLoading={isComparing}
                            onPress={handleCompare}
                            isDisabled={!file || selectedModels.length === 0}
                        >
                            Compare {selectedModels.length} Models
                        </Button>
                    </div>
                </CardBody>
            </Card>

            {/* Error Message */}
            {result?.error && (
                <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 p-4 rounded-lg flex items-center gap-3 text-red-600 dark:text-red-400">
                    <XCircle size={20} />
                    <div>
                        <p className="font-bold">Comparison Failed</p>
                        <p className="text-sm">{result.error}</p>
                    </div>
                </div>
            )}

            {/* Loading State */}
            {isComparing && (
                <div className="text-center py-12 bg-white dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/10">
                    <Loader2 size={48} className="mx-auto mb-4 animate-spin text-purple-500" />
                    <h3 className="text-xl font-bold mb-2">Running Comparison...</h3>
                    <p className="text-gray-500 dark:text-white/50">
                        Testing {selectedModels.length} Gemini models. This may take 10-20 seconds.
                    </p>
                </div>
            )}

            {/* Results */}
            {result && !result.error && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                        <CardBody className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-bold">🔬 Gemini Model Comparison Results</h3>
                                {result.winner && (
                                    <Chip color="success" variant="flat">
                                        <Trophy className="inline w-4 h-4 mr-1" /> Winner: {result.winner.model_id}
                                    </Chip>
                                )}
                            </div>

                            {/* Summary Stats */}
                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div className="bg-purple-50 dark:bg-purple-500/10 p-3 rounded-lg text-center">
                                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{result.models_tested}</p>
                                    <p className="text-xs text-purple-700 dark:text-purple-300">Models Tested</p>
                                </div>
                                <div className="bg-blue-50 dark:bg-blue-500/10 p-3 rounded-lg text-center">
                                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{result.total_duration_ms}ms</p>
                                    <p className="text-xs text-blue-700 dark:text-blue-300">Total Time</p>
                                </div>
                                <div className="bg-green-50 dark:bg-green-500/10 p-3 rounded-lg text-center">
                                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">${result.total_cost?.toFixed(4)}</p>
                                    <p className="text-xs text-green-700 dark:text-green-300">Total Cost</p>
                                </div>
                            </div>

                            {/* Results Table */}
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm border border-gray-200 dark:border-white/10 rounded-lg overflow-hidden text-gray-900 dark:text-gray-100">
                                    <thead className="bg-gray-100 dark:bg-white/5 text-gray-900 dark:text-gray-100">
                                        <tr>
                                            <th className="text-left py-3 px-4 font-bold">Model</th>
                                            <th className="text-center py-3 px-4 font-bold">Status</th>
                                            <th className="text-center py-3 px-4 font-bold">Deals</th>
                                            <th className="text-center py-3 px-4 font-bold">Duration</th>
                                            <th className="text-center py-3 px-4 font-bold">Est. Cost</th>
                                            <th className="text-center py-3 px-4 font-bold">Log</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200 dark:divide-white/5">
                                        {Object.entries(result.results || {}).map(([modelId, data]: [string, any]) => (
                                            <tr key={modelId} className={`${result.winner?.model_id === modelId ? 'bg-green-50 dark:bg-green-500/10' : 'bg-white dark:bg-transparent'}`}>
                                                <td className="py-3 px-4 font-medium">{modelId}</td>
                                                <td className="text-center">
                                                    {data.success ? (
                                                        <CheckCircle size={18} className="inline text-green-500" />
                                                    ) : (
                                                        <XCircle size={18} className="inline text-red-500" />
                                                    )}
                                                </td>
                                                <td className="text-center font-bold text-lg">{data.deal_count}</td>
                                                <td className="text-center">{data.duration_ms}ms</td>
                                                <td className="text-center text-purple-600 dark:text-purple-400">
                                                    ${data.estimated_cost?.toFixed(6) || '0'}
                                                </td>
                                                <td className="text-center">
                                                    <Button
                                                        size="sm"
                                                        variant="flat"
                                                        isIconOnly
                                                        onPress={() => showLog(data.raw_input || "", data.raw_response || "")}
                                                    >
                                                        <FileText size={14} />
                                                    </Button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Sample Deals from Winner */}
                            {result.winner && result.results[result.winner.model_id]?.deals?.length > 0 && (
                                <div className="mt-6 p-4 bg-gray-50 dark:bg-white/5 rounded-lg">
                                    <p className="text-sm font-bold mb-2">Sample Deals from {result.winner.model_id}:</p>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                        {result.results[result.winner.model_id].deals.slice(0, 4).map((deal: any, i: number) => (
                                            <div key={i} className="bg-white dark:bg-white/5 p-2 rounded border border-gray-200 dark:border-white/10">
                                                <p className="font-medium text-sm truncate">{deal.product_name}</p>
                                                <p className="text-purple-600 dark:text-purple-400 font-bold">€{deal.price}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardBody>
                    </Card>
                </motion.div>
            )}

            {/* Model Info */}
            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-6">
                    <h3 className="font-bold mb-4 flex items-center gap-2"><ChartBar size={18} /> Gemini Model Comparison (For Coursework)</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-200 dark:border-white/10">
                                    <th className="text-left py-2 px-3">Model</th>
                                    <th className="text-center py-2 px-3">Speed</th>
                                    <th className="text-center py-2 px-3">Cost</th>
                                    <th className="text-left py-2 px-3">Best For</th>
                                </tr>
                            </thead>
                            <tbody className="text-gray-600 dark:text-white/70">
                                <tr className="border-b border-gray-100 dark:border-white/5">
                                    <td className="py-2 px-3 font-medium">Gemini 2.5 Flash</td>
                                    <td className="text-center">⚡⚡⚡</td>
                                    <td className="text-center text-green-600">$</td>
                                    <td>High-speed production</td>
                                </tr>
                                <tr className="border-b border-gray-100 dark:border-white/5">
                                    <td className="py-2 px-3 font-medium">Gemini 2.5 Pro</td>
                                    <td className="text-center">⚡⚡</td>
                                    <td className="text-center text-green-600">$$</td>
                                    <td>Complex reasoning tasks</td>
                                </tr>
                                <tr className="border-b border-gray-100 dark:border-white/5">
                                    <td className="py-2 px-3 font-medium">Gemini 3 Flash</td>
                                    <td className="text-center">⚡⚡⚡⚡</td>
                                    <td className="text-center text-green-600">$</td>
                                    <td>Next-gen speed</td>
                                </tr>
                                <tr>
                                    <td className="py-2 px-3 font-medium">Gemini 3 Pro</td>
                                    <td className="text-center">⚡⚡</td>
                                    <td className="text-center text-orange-600">$$$</td>
                                    <td>Advanced multimodal reasoning</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </CardBody>
            </Card>

        </div>
    );
}


function AuditLogsTab({ logs, onViewDetail, onRefresh }: { logs: any[], onViewDetail: (id: number) => void, onRefresh: () => void }) {
    if (!logs) return <div className="p-8 text-center text-gray-500">Loading logs...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <Activity className="w-6 h-6 text-blue-500" /> System Audit Logs
                </h2>
                <Button size="sm" variant="flat" onPress={onRefresh} startContent={<Clock size={14} />}>
                    Refresh
                </Button>
            </div>

            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-100 dark:bg-white/5 border-b border-gray-200 dark:border-white/10">
                                <tr>
                                    <th className="p-3 text-left font-semibold">Timestamp</th>
                                    <th className="p-3 text-left font-semibold">Feature</th>
                                    <th className="p-3 text-left font-semibold">Model</th>
                                    <th className="p-3 text-left font-semibold">Tokens</th>
                                    <th className="p-3 text-left font-semibold">Latency</th>
                                    <th className="p-3 text-left font-semibold">Cost</th>
                                    <th className="p-3 text-left font-semibold">Status</th>
                                    <th className="p-3 text-left font-semibold">Ref</th>
                                    <th className="p-3 text-right font-semibold">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 dark:divide-white/5">
                                {logs.map((log) => (
                                    <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-white/5">
                                        <td className="p-3 whitespace-nowrap text-xs text-gray-500">{new Date(log.timestamp).toLocaleString()}</td>
                                        <td className="p-3 font-medium">{log.feature}</td>
                                        <td className="p-3">
                                            <Chip size="sm" variant="flat" color="primary">{log.model}</Chip>
                                        </td>
                                        <td className="p-3 text-gray-500">{log.tokens_used?.toLocaleString()}</td>
                                        <td className="p-3 text-gray-500">{log.latency_ms}ms</td>
                                        <td className="p-3 font-mono text-green-600 dark:text-green-400">
                                            ${log.cost_usd > 0 ? log.cost_usd.toFixed(6) : "0.00"}
                                        </td>
                                        <td className="p-3">
                                            <Chip size="sm" color={log.status === 'success' ? 'success' : log.status === 'cached' ? 'secondary' : 'danger'} variant="dot">
                                                {log.status}
                                            </Chip>
                                        </td>
                                        <td className="p-3 text-xs flex gap-1">
                                            {log.image_present ? <Camera size={14} className="text-purple-500" /> : null}
                                        </td>
                                        <td className="p-3 text-right">
                                            <Button size="sm" variant="light" isIconOnly onPress={() => onViewDetail(log.id)}>
                                                <FileText size={16} />
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardBody>
            </Card>
        </div>
    );
}

function LogDetailModal({ isOpen, onOpenChange, log }: { isOpen: boolean, onOpenChange: () => void, log: any }) {
    if (!log) return null;

    return (
        <Modal
            isOpen={isOpen}
            onOpenChange={onOpenChange}
            size="5xl"
            scrollBehavior="inside"
            classNames={{
                base: "bg-white dark:bg-slate-900 border border-gray-200 dark:border-white/10",
                header: "border-b border-gray-200 dark:border-white/10",
                footer: "border-t border-gray-200 dark:border-white/10"
            }}
        >
            <ModalContent>
                {(onClose) => (
                    <>
                        <ModalHeader className="flex flex-col gap-1">
                            <div className="flex items-center gap-2">
                                <Activity size={20} className="text-blue-500" />
                                <span>Audit Log Detail #{log.id}</span>
                                <Chip size="sm" color={log.status === 'success' ? 'success' : 'danger'}>{log.status}</Chip>
                            </div>
                            <div className="text-xs font-normal text-gray-500">
                                {new Date(log.timestamp).toLocaleString()} • {log.model} • {log.feature}
                            </div>
                        </ModalHeader>
                        <ModalBody className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
                                <div className="flex flex-col h-full">
                                    <div className="flex justify-between items-center mb-2">
                                        <h3 className="font-bold flex items-center gap-2"><div className="w-2 h-2 bg-blue-500 rounded-full"></div> Input (Prompt)</h3>
                                        <span className="text-xs text-gray-500">{log.prompt_chars} chars</span>
                                    </div>
                                    <div className="flex-grow bg-gray-50 dark:bg-black/20 rounded-lg p-4 font-mono text-xs overflow-auto border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-[500px]">
                                        {log.raw_input || "(No input recorded)"}
                                    </div>
                                </div>
                                <div className="flex flex-col h-full">
                                    <div className="flex justify-between items-center mb-2">
                                        <h3 className="font-bold flex items-center gap-2"><div className="w-2 h-2 bg-green-500 rounded-full"></div> Output (Response)</h3>
                                        <span className="text-xs text-gray-500">{log.response_chars} chars</span>
                                    </div>
                                    <div className="flex-grow bg-gray-50 dark:bg-black/20 rounded-lg p-4 font-mono text-xs overflow-auto border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-[500px]">
                                        {log.raw_output || "(No output recorded)"}
                                    </div>
                                </div>
                            </div>

                            {log.error_msg && (
                                <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-500/20 rounded-lg text-red-600 dark:text-red-400 text-sm font-mono">
                                    <strong>Error:</strong> {log.error_msg}
                                </div>
                            )}
                        </ModalBody>
                        <ModalFooter>
                            <div className="flex-1 text-xs text-gray-500">
                                Cost: ${log.cost_usd > 0 ? log.cost_usd.toFixed(6) : "0.00"} • Latency: {log.latency_ms}ms • Tokens: {log.tokens_used}
                            </div>
                            <Button color="primary" onPress={onClose}>
                                Close
                            </Button>
                        </ModalFooter>
                    </>
                )}
            </ModalContent>
        </Modal>
    );
}

// Deals Manager Component
function DealsManager() {
    const [deals, setDeals] = useState<any[]>([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(false);
    // Selection state
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

    const { isOpen, onOpen, onOpenChange } = useDisclosure();
    const [newDeal, setNewDeal] = useState({ product_name: "", price: "", store: "", category: "General" });

    useEffect(() => {
        loadDeals();
    }, [page, search]);

    const loadDeals = async () => {
        setLoading(true);
        try {
            const data = await searchDeals(search, page);
            setDeals(data.deals || []);
            setTotalPages(data.pages || 1);
            setSelectedIds(new Set()); // Reset selection on page change
        } catch (e) {
            console.error("Failed to load deals", e);
        }
        setLoading(false);
    };

    const handleSelectAll = (checked: boolean) => {
        if (checked) {
            setSelectedIds(new Set(deals.map(d => d.id)));
        } else {
            setSelectedIds(new Set());
        }
    };

    const handleSelectRow = (id: number, checked: boolean) => {
        const next = new Set(selectedIds);
        if (checked) next.add(id);
        else next.delete(id);
        setSelectedIds(next);
    };

    const handleBulkDelete = async () => {
        const ids = Array.from(selectedIds);
        if (confirm(`Permanently delete ${ids.length} selected deals?`)) {
            try {
                await deleteDealsBatch(ids);
                loadDeals(); // Reload and clear selection
            } catch (e) {
                alert("Failed to delete selection");
            }
        }
    };

    const handleCreate = async () => {
        await createDeal(newDeal);
        onOpenChange(); // Close modal
        setNewDeal({ product_name: "", price: "", store: "", category: "General" });
        loadDeals();
    };

    const handleUpdate = async (id: number, updates: any) => {
        try {
            const res = await fetch(`${API}/deals/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            if (res.ok) {
                setDeals(deals.map(d => d.id === id ? { ...d, ...updates } : d));
            }
        } catch (e) {
            alert("Failed to save changes");
        }
    };

    const handleDelete = async (id: number) => {
        if (confirm("Permanently delete this deal?")) {
            try {
                await deleteDeal(id);
                loadDeals();
            } catch (e) {
                alert("Failed to delete deal");
            }
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center bg-white dark:bg-white/5 p-4 rounded-lg border border-gray-200 dark:border-white/10">
                <div className="flex gap-4 items-center flex-1">
                    <Input
                        placeholder="Search deals..."
                        value={search}
                        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                        startContent={<Eye size={16} className="text-gray-400" />}
                        className="max-w-md"
                    />
                    {selectedIds.size > 0 ? (
                        <Button color="danger" variant="flat" onPress={handleBulkDelete} startContent={<Trash2 size={16} />}>
                            Delete Selected ({selectedIds.size})
                        </Button>
                    ) : (
                        <Button color="primary" onPress={onOpen} startContent={<CheckCircle size={16} />}>
                            Add Manual Deal
                        </Button>
                    )}
                </div>
            </div>

            <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                <CardBody className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-100 dark:bg-white/5 border-b border-gray-200 dark:border-white/10">
                                <tr>
                                    <th className="p-3 text-left font-semibold w-10">
                                        <input
                                            type="checkbox"
                                            checked={deals.length > 0 && selectedIds.size === deals.length}
                                            onChange={(e) => handleSelectAll(e.target.checked)}
                                            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                    </th>
                                    <th className="p-3 text-left font-semibold">Product</th>
                                    <th className="p-3 text-left font-semibold">Price</th>
                                    <th className="p-3 text-left font-semibold">Store</th>
                                    <th className="p-3 text-left font-semibold">Category / Edit</th>
                                    <th className="p-3 text-right font-semibold">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 dark:divide-white/5">
                                {loading && <tr><td colSpan={6} className="p-8 text-center text-gray-500">Loading...</td></tr>}
                                {!loading && deals.map((deal) => (
                                    <EditableRow
                                        key={deal.id}
                                        deal={deal}
                                        onSave={handleUpdate}
                                        onDelete={handleDelete}
                                        selected={selectedIds.has(deal.id)}
                                        onSelect={handleSelectRow}
                                    />
                                ))}
                                {!loading && deals.length === 0 && (
                                    <tr><td colSpan={6} className="p-8 text-center text-gray-500">No deals found</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardBody>
            </Card>

            <div className="flex justify-center gap-2 mt-4">
                <Button size="sm" isDisabled={page === 1} onPress={() => setPage(page - 1)}>Prev</Button>
                <div className="flex items-center text-sm text-gray-500">Page {page} of {totalPages}</div>
                <Button size="sm" isDisabled={page === totalPages} onPress={() => setPage(page + 1)}>Next</Button>
            </div>

            {/* Create Deal Modal */}
            <Modal isOpen={isOpen} onOpenChange={onOpenChange}>
                <ModalContent>
                    {(onClose) => (
                        <>
                            <ModalHeader>Add New Deal</ModalHeader>
                            <ModalBody>
                                <Input label="Product Name" value={newDeal.product_name} onChange={(e) => setNewDeal({ ...newDeal, product_name: e.target.value })} />
                                <Input label="Price (e.g. 1.99)" value={newDeal.price} onChange={(e) => setNewDeal({ ...newDeal, price: e.target.value })} />
                                <Input label="Store" value={newDeal.store} onChange={(e) => setNewDeal({ ...newDeal, store: e.target.value })} />
                                <Input label="Category" value={newDeal.category} onChange={(e) => setNewDeal({ ...newDeal, category: e.target.value })} />
                            </ModalBody>
                            <ModalFooter>
                                <Button variant="light" onPress={onClose}>Cancel</Button>
                                <Button color="primary" onPress={handleCreate}>Create</Button>
                            </ModalFooter>
                        </>
                    )}
                </ModalContent>
            </Modal>
        </div>
    );
}

function DataManagementTab({ uploads, onViewDeals, onDelete, onRefresh }: { uploads: any[], onViewDeals: (u: any) => void, onDelete: (id: number) => void, onRefresh: () => void }) {
    const [view, setView] = useState<'uploads' | 'deals'>('uploads');
    const [syntheticCount, setSyntheticCount] = useState<number>(0);
    const [showSynthetic, setShowSynthetic] = useState<boolean>(true);

    useEffect(() => {
        loadSyntheticCount();
        loadVisibility();
    }, []);

    const loadSyntheticCount = async () => {
        try {
            const res = await fetchSyntheticCount();
            setSyntheticCount(res.count);
        } catch (e) { console.error(e); }
    };

    const loadVisibility = async () => {
        try {
            const res = await fetchSyntheticVisibility();
            setShowSynthetic(res.show);
        } catch (e) { console.error(e); }
    };

    const toggleVisibility = async (val: boolean) => {
        setShowSynthetic(val);
        await setSyntheticVisibility(val);
    };

    const handleClearSynthetic = async () => {
        if (confirm(`Are you sure you want to delete all ${syntheticCount} synthetic deals? This cannot be undone.`)) {
            await deleteSyntheticData();
            loadSyntheticCount();
            alert("Synthetic data cleared.");
        }
    };


    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex gap-4">
                    <button
                        onClick={() => setView('uploads')}
                        className={`text-lg font-bold flex items-center gap-2 ${view === 'uploads' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'}`}
                    >
                        <Database className="w-5 h-5" /> Upload History
                    </button>
                    <button
                        onClick={() => setView('deals')}
                        className={`text-lg font-bold flex items-center gap-2 ${view === 'deals' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'}`}
                    >
                        <ShoppingBag className="w-5 h-5" /> All Deals (Manager)
                    </button>
                </div>
                <div className="flex gap-2">
                    {/* Visibility Toggle */}
                    <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-white/5 rounded-lg">
                        <span className="text-xs font-medium text-gray-500">Show Mock Data</span>
                        <Switch size="sm" isSelected={showSynthetic} onValueChange={toggleVisibility} />
                    </div>
                    {(syntheticCount > 0) && (
                        <Button size="sm" color="danger" variant="flat" onPress={handleClearSynthetic} startContent={<Trash2 size={14} />}>
                            Clear Mock ({syntheticCount})
                        </Button>
                    )}
                    <Button size="sm" variant="flat" onPress={onRefresh} startContent={<Clock size={14} />}>
                        Refresh
                    </Button>
                </div>
            </div>

            {view === 'uploads' ? (
                <Card className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10">
                    <CardBody className="p-0">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-100 dark:bg-white/5 border-b border-gray-200 dark:border-white/10">
                                    <tr>
                                        <th className="p-3 text-left font-semibold">ID</th>
                                        <th className="p-3 text-left font-semibold">Filename</th>
                                        <th className="p-3 text-left font-semibold">Date</th>
                                        <th className="p-3 text-left font-semibold">Deals</th>
                                        <th className="p-3 text-right font-semibold">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100 dark:divide-white/5">
                                    {uploads.map((upload) => (
                                        <tr key={upload.id} className="hover:bg-gray-50 dark:hover:bg-white/5">
                                            <td className="p-3 text-gray-500">#{upload.id}</td>
                                            <td className="p-3 font-medium flex items-center gap-2">
                                                <FileText size={16} className="text-gray-400" />
                                                {upload.filename}
                                            </td>
                                            <td className="p-3 text-gray-500">{new Date(upload.timestamp).toLocaleString()}</td>
                                            <td className="p-3">
                                                <Chip size="sm" variant="flat" color="secondary">{upload.deal_count} Items</Chip>
                                            </td>
                                            <td className="p-3 text-right flex justify-end gap-2">
                                                <Button size="sm" variant="light" isIconOnly onPress={() => onViewDeals(upload)} title="View Deals">
                                                    <Eye size={18} className="text-blue-500" />
                                                </Button>
                                                <Button size="sm" variant="light" color="danger" isIconOnly onPress={() => onDelete(upload.id)} title="Delete Upload">
                                                    <Trash2 size={18} />
                                                </Button>
                                            </td>
                                        </tr>
                                    ))}
                                    {uploads.length === 0 && (
                                        <tr>
                                            <td colSpan={5} className="p-8 text-center text-gray-500">No uploads found</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </CardBody>
                </Card>
            ) : (
                <DealsManager />
            )}
        </div>
    );
}

// Editable Row Component
const EditableRow = ({
    deal,
    onSave,
    onDelete,
    selected,
    onSelect
}: {
    deal: any,
    onSave: (id: number, updates: any) => Promise<void>,
    onDelete?: (id: number) => void,
    selected?: boolean,
    onSelect?: (id: number, val: boolean) => void
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [data, setData] = useState({ ...deal });
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        await onSave(deal.id, data);
        setSaving(false);
        setIsEditing(false);
    };

    if (!isEditing) {
        return (
            <tr className={`hover:bg-gray-50 dark:hover:bg-white/5 group ${selected ? 'bg-blue-50/50 dark:bg-blue-900/20' : ''}`}>
                {onSelect && (
                    <td className="p-3 w-10">
                        <input
                            type="checkbox"
                            checked={selected}
                            onChange={(e) => onSelect(deal.id, e.target.checked)}
                            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                    </td>
                )}
                <td className="p-3">
                    <div className="flex items-center gap-3">
                        <div>
                            <div className="font-medium">{deal.product_name}</div>
                            <div className="text-[10px] text-gray-400">{new Date(deal.created_at || Date.now()).toLocaleDateString()}</div>
                        </div>
                    </div>
                </td>
                <td className="p-3 font-bold text-green-600 dark:text-green-400">
                    {deal.price} €
                    {deal.original_price && <span className="text-gray-400 font-normal text-xs ml-1 line-through">{deal.original_price}</span>}
                </td>
                <td className="p-3 text-gray-500">{deal.store}</td>
                <td className="p-3">
                    <div className="flex justify-between items-center">
                        <Chip size="sm" variant="dot" color="default">{deal.category}</Chip>
                        <Button isIconOnly size="sm" variant="light" className="opacity-0 group-hover:opacity-100" onPress={() => setIsEditing(true)}>
                            <Pencil size={14} />
                        </Button>
                    </div>
                </td>
                {onSelect && (
                    <td className="p-3 text-right">
                        {onDelete && (
                            <Button isIconOnly size="sm" variant="light" color="danger" onPress={() => onDelete(deal.id)}>
                                <Trash2 size={16} className="text-gray-400 hover:text-red-500" />
                            </Button>
                        )}
                    </td>
                )}
            </tr>
        );
    }

    return (
        <tr className="bg-blue-50 dark:bg-blue-900/10">
            {onSelect && <td className="p-3"></td>}
            <td className="p-3">
                <Input
                    size="sm"
                    value={data.product_name}
                    onChange={(e) => setData({ ...data, product_name: e.target.value })}
                    label="Product"
                />
            </td>
            <td className="p-3 w-32">
                <Input
                    size="sm"
                    value={data.price}
                    onChange={(e) => setData({ ...data, price: e.target.value })}
                    label="Price"
                />
            </td>
            <td className="p-3 w-40">
                <Input
                    size="sm"
                    value={data.store}
                    onChange={(e) => setData({ ...data, store: e.target.value })}
                    label="Store"
                />
            </td>
            <td className="p-3 text-right" colSpan={onSelect ? 2 : 1}>
                <div className="flex gap-1 justify-end">
                    <Button size="sm" color="primary" isIconOnly onPress={handleSave} isLoading={saving}>
                        <Check size={14} />
                    </Button>
                    <Button size="sm" variant="flat" isIconOnly onPress={() => setIsEditing(false)}>
                        <X size={14} />
                    </Button>
                </div>
            </td>
        </tr>
    );
};

function ViewDealsModal({ isOpen, onClose, upload }: { isOpen: boolean, onClose: () => void, upload: any }) {
    const [deals, setDeals] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen && upload) {
            setLoading(true);
            fetch(`${API}/uploads/${upload.id}/deals`)
                .then(res => res.json())
                .then(data => {
                    setDeals(data.deals || []);
                    setLoading(false);
                })
                .catch(() => setLoading(false));
        }
    }, [isOpen, upload]);

    const handleUpdate = async (id: number, updates: any) => {
        try {
            const res = await fetch(`${API}/deals/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            if (res.ok) {
                setDeals(deals.map(d => d.id === id ? { ...d, ...updates } : d));
            }
        } catch (e) {
            alert("Failed to save changes");
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="3xl" scrollBehavior="inside">
            <ModalContent>
                {(onClose) => (
                    <>
                        <ModalHeader className="flex flex-col gap-1">
                            Deals from {upload?.filename}
                            <span className="text-xs font-normal text-gray-500">
                                {deals.length} items found
                            </span>
                        </ModalHeader>
                        <ModalBody>
                            {loading ? (
                                <div className="flex justify-center p-8"><Spinner /></div>
                            ) : (
                                <div className="border border-gray-200 dark:border-white/10 rounded-lg overflow-hidden">
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-50 dark:bg-white/5 border-b border-gray-200 dark:border-white/10 sticky top-0 z-10">
                                            <tr>
                                                <th className="p-3 text-left font-semibold">Product</th>
                                                <th className="p-3 text-left font-semibold">Price</th>
                                                <th className="p-3 text-left font-semibold">Store</th>
                                                <th className="p-3 text-left font-semibold">Category / Edit</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100 dark:divide-white/5">
                                            {deals.map((deal) => (
                                                <EditableRow key={deal.id} deal={deal} onSave={handleUpdate} />
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </ModalBody>
                        <ModalFooter>
                            <Button color="primary" onPress={onClose}>
                                Close
                            </Button>
                        </ModalFooter>
                    </>
                )}
            </ModalContent>
        </Modal>
    );
}
