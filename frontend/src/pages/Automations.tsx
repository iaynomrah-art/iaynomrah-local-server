import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";
import { Layout } from "@/components/Layout";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    RefreshCw,
    Plus,
    Trash2,
    Edit,
    Package,
    FileText,
    Clock,
    MoreVertical,
    Upload,
    Search,
    Play,
    Loader2
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface Automation {
    id: string;
    name: string;
    description?: string;
    file_name: string;
    path: string;
    created_at: string;
}

const Automations = () => {
    const queryClient = useQueryClient();
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    const { data: automations, isLoading, isError } = useQuery<Automation[]>({
        queryKey: ["automations"],
        queryFn: async () => {
            const response = await axios.get("/api/v1/automation");
            return response.data;
        },
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: string) => {
            await axios.delete(`/api/v1/automation/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["automations"] });
            toast.success("Automation deleted successfully");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Delete failed");
        },
    });

    const addMutation = useMutation({
        mutationFn: async (formData: FormData) => {
            const response = await axios.post("/api/v1/automation", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["automations"] });
            toast.success("Automation added successfully");
            setIsAddOpen(false);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Add failed");
        },
    });

    const syncMutation = useMutation({
        mutationFn: async () => {
            const response = await axios.post("/api/v1/automation/sync");
            return response.data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["automations"] });
            toast.success(data.message);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Sync failed");
        },
    });

    const runMutation = useMutation({
        mutationFn: async (identifier: string) => {
            // Identifier can be the automation ID or file_name
            const response = await axios.post(`/api/v1/runner/${identifier}`, {});
            return response.data;
        },
        onSuccess: (data, identifier) => {
            toast.success(`Successfully triggered automation: ${identifier}`);
            console.log("Execution Result:", data);
        },
        onError: (error: any) => {
            const detail = error.response?.data?.detail;
            toast.error(typeof detail === 'string' ? detail : "Execution failed. Check if UiRobot path is correct.");
        },
    });

    const handleAdd = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const file = formData.get("file") as File;
        if (!file || file.size === 0) {
            toast.error("Please upload a .nupkg file");
            return;
        }
        addMutation.mutate(formData);
    };

    const filteredAutomations = Array.isArray(automations)
        ? automations.filter(a =>
            a.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            a.file_name?.toLowerCase().includes(searchQuery.toLowerCase())
        )
        : [];

    return (
        <Layout>
            <div className="space-y-6 max-w-7xl mx-auto w-full">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                            Automations
                        </h2>
                        <p className="text-muted-foreground mt-1">
                            Manage your published UiPath automation packages.
                        </p>
                    </div>

                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            className="rounded-xl border-primary/20 hover:bg-primary/5 transition-all"
                            onClick={() => syncMutation.mutate()}
                            disabled={syncMutation.isPending || isLoading}
                        >
                            <RefreshCw className={`w-4 h-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                            Sync Folder
                        </Button>

                        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                            <DialogTrigger asChild>
                                <Button className="rounded-xl px-6 shadow-lg shadow-primary/20 transition-all hover:scale-[1.02] active:scale-[0.98]">
                                    <Plus className="w-4 h-4 mr-2" /> Add Package
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[500px] p-6">
                                <form onSubmit={handleAdd} className="space-y-6">
                                    <DialogHeader>
                                        <DialogTitle className="text-2xl font-bold flex items-center gap-2">
                                            <Upload className="w-6 h-6 text-primary" />
                                            New Automation
                                        </DialogTitle>
                                        <DialogDescription>
                                            Upload a .nupkg file to add it to the orchestration list.
                                        </DialogDescription>
                                    </DialogHeader>
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="name" className="text-sm font-semibold">Package Alias (Optional)</Label>
                                            <Input id="name" name="name" placeholder="Friendly name for this automation" className="rounded-xl" />
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="description" className="text-sm font-semibold">Description</Label>
                                            <Textarea id="description" name="description" placeholder="What does this robot do?" className="rounded-xl min-h-[100px]" />
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="file" className="text-sm font-semibold">Automation File (.nupkg)</Label>
                                            <div className="border-2 border-dashed border-border/50 rounded-xl p-8 transition-colors hover:border-primary/50 group relative">
                                                <Input
                                                    id="file"
                                                    name="file"
                                                    type="file"
                                                    accept=".nupkg"
                                                    className="absolute inset-0 opacity-0 cursor-pointer z-10"
                                                />
                                                <div className="flex flex-col items-center justify-center text-center space-y-2">
                                                    <div className="p-3 bg-secondary rounded-full group-hover:bg-primary/10 transition-colors">
                                                        <Package className="w-6 h-6 text-muted-foreground group-hover:text-primary transition-colors" />
                                                    </div>
                                                    <p className="text-sm font-medium">Click or drag package here</p>
                                                    <p className="text-xs text-muted-foreground">Only .nupkg files are supported</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <DialogFooter className="pt-4">
                                        <Button type="button" variant="ghost" onClick={() => setIsAddOpen(false)} disabled={addMutation.isPending}>
                                            Cancel
                                        </Button>
                                        <Button type="submit" disabled={addMutation.isPending} className="px-8 rounded-xl shadow-lg shadow-primary/20">
                                            {addMutation.isPending ? "Uploading..." : "Publish Automation"}
                                        </Button>
                                    </DialogFooter>
                                </form>
                            </DialogContent>
                        </Dialog>
                    </div>
                </div>

                <Card className="border-border/40 shadow-xl shadow-foreground/5 bg-card/50 backdrop-blur-sm overflow-hidden rounded-2xl">
                    <CardHeader className="bg-secondary/20 pb-4 border-b">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="space-y-1">
                                <CardTitle className="text-lg">Package Inventory</CardTitle>
                                <CardDescription>Total automations: {automations?.length || 0}</CardDescription>
                            </div>
                            <div className="relative w-full md:w-80">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search automations..."
                                    className="pl-10 rounded-xl bg-background/50 border-border/50 transition-all focus:ring-primary/20"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="p-0">
                        {isLoading ? (
                            <div className="p-8 space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <Skeleton key={i} className="h-16 w-full rounded-xl" />
                                ))}
                            </div>
                        ) : isError ? (
                            <div className="p-12 text-center space-y-4">
                                <div className="p-4 bg-destructive/10 rounded-full w-fit mx-auto text-destructive">
                                    <Package className="w-8 h-8" />
                                </div>
                                <h3 className="font-bold text-xl">Connection Error</h3>
                                <p className="text-muted-foreground">Unable to fetch automations from the server.</p>
                                <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ["automations"] })}>
                                    Try Again
                                </Button>
                            </div>
                        ) : filteredAutomations?.length === 0 ? (
                            <div className="p-20 text-center space-y-6">
                                <div className="relative w-24 h-24 mx-auto mb-4">
                                    <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
                                    <div className="relative bg-secondary p-6 rounded-full inline-block border-2 border-border/50">
                                        <Package className="w-10 h-10 text-muted-foreground" />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-2xl font-bold tracking-tight">No Automations Found</h3>
                                    <p className="text-muted-foreground max-w-sm mx-auto">
                                        {searchQuery ? `No results for "${searchQuery}"` : "Get started by publishing your first robot package."}
                                    </p>
                                </div>
                                {!searchQuery && (
                                    <Button variant="outline" className="rounded-xl px-10 border-primary/30 text-primary hover:bg-primary/5" onClick={() => setIsAddOpen(true)}>
                                        Publish first robot
                                    </Button>
                                )}
                            </div>
                        ) : (
                            <Table>
                                <TableHeader className="bg-secondary/10">
                                    <TableRow className="hover:bg-transparent border-border/40">
                                        <TableHead className="w-12"></TableHead>
                                        <TableHead className="font-bold text-xs uppercase tracking-wider py-4">Package Identity</TableHead>
                                        <TableHead className="font-bold text-xs uppercase tracking-wider py-4">File Name</TableHead>
                                        <TableHead className="font-bold text-xs uppercase tracking-wider py-4">Status</TableHead>
                                        <TableHead className="text-right font-bold text-xs uppercase tracking-wider py-4 px-6">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredAutomations?.map((automation) => (
                                        <TableRow
                                            key={automation.id}
                                            className="group border-border/40 hover:bg-secondary/20 transition-colors"
                                        >
                                            <TableCell className="text-center pl-6">
                                                <div className="bg-primary/10 p-2 rounded-lg group-hover:scale-110 transition-transform">
                                                    <Package className="w-5 h-5 text-primary" />
                                                </div>
                                            </TableCell>
                                            <TableCell className="py-5">
                                                <div className="font-bold text-foreground text-base">{automation.name}</div>
                                                <div className="text-sm text-muted-foreground line-clamp-1 max-w-xs flex items-center gap-1.5">
                                                    <FileText className="w-3 h-3" /> {automation.description || "No description provided"}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <code className="text-[10px] bg-muted px-2 py-1 rounded-md text-muted-foreground font-mono">
                                                    {automation.file_name}
                                                </code>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className="rounded-lg font-bold border-primary/20 bg-primary/5 text-primary text-[10px] py-0.5 px-2">
                                                    ACTIVE
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-right px-6">
                                                <div className="flex items-center justify-end gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-8 w-8 hover:bg-green-500/10 border border-border/0 hover:border-green-500/30 transition-all group/run"
                                                        onClick={() => runMutation.mutate(automation.id)}
                                                        disabled={runMutation.isPending}
                                                        title="Run Automation"
                                                    >
                                                        {runMutation.isPending && runMutation.variables === automation.id ? (
                                                            <Loader2 className="h-4 w-4 animate-spin text-green-600" />
                                                        ) : (
                                                            <Play className="h-4 w-4 text-muted-foreground group-hover/run:text-green-600 transition-colors" />
                                                        )}
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-8 w-8 hover:bg-background shadow-sm border border-border/0 hover:border-border/50 transition-all"
                                                        onClick={() => toast.info("Edit feature coming soon!")}
                                                    >
                                                        <Edit className="h-4 w-4 text-muted-foreground hover:text-primary transition-colors" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-8 w-8 hover:bg-destructive/10 border border-border/0 hover:border-destructive/30 transition-all"
                                                        onClick={() => {
                                                            if (confirm("Are you sure you want to delete this automation?")) {
                                                                deleteMutation.mutate(automation.id);
                                                            }
                                                        }}
                                                    >
                                                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive transition-colors" />
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </div>
        </Layout>
    );
};

export default Automations;
