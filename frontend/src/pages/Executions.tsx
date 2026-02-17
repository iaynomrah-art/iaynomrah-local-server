import { useQuery } from "@tanstack/react-query";
import axios from "axios";
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
import {
    Clock,
    PlayCircle,
    CheckCircle2,
    XCircle,
    Info,
    Terminal,
    ChevronDown,
    ChevronUp
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useState } from "react";
import { Button } from "@/components/ui/button";

interface ExecutionHistory {
    id: number;
    created_at: string;
    automation_id: string;
    automation_name: string;
    input: any;
    status: string;
    stdout?: string;
    stderr?: string;
    exit_code?: number;
    message?: string;
}

const Executions = () => {
    const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

    const { data: history, isLoading, isError, refetch } = useQuery<ExecutionHistory[]>({
        queryKey: ["execution-history"],
        queryFn: async () => {
            const response = await axios.get("/api/v1/automation/history");
            return response.data;
        },
        refetchInterval: 5000, // Refresh every 5 seconds
    });

    const toggleRow = (id: number) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedRows(newExpanded);
    };

    const getStatusBadge = (status: string) => {
        switch (status?.toLowerCase()) {
            case "success":
                return <Badge className="bg-green-500/10 text-green-500 border-green-500/20 hover:bg-green-500/20">Success</Badge>;
            case "error":
                return <Badge className="bg-red-500/10 text-red-500 border-red-500/20 hover:bg-red-500/20">Error</Badge>;
            default:
                return <Badge variant="secondary">{status || "Unknown"}</Badge>;
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status?.toLowerCase()) {
            case "success":
                return <CheckCircle2 className="w-4 h-4 text-green-500" />;
            case "error":
                return <XCircle className="w-4 h-4 text-red-500" />;
            default:
                return <Clock className="w-4 h-4 text-muted-foreground" />;
        }
    };

    return (
        <Layout>
            <div className="space-y-6 max-w-7xl mx-auto w-full">
                <div className="flex justify-between items-center">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                            Executions
                        </h2>
                        <p className="text-muted-foreground mt-1">
                            Monitor and track your automation runs in real-time.
                        </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => refetch()}>
                        Refresh
                    </Button>
                </div>

                <Card className="border-border/40 shadow-xl bg-card/50 backdrop-blur-sm rounded-2xl overflow-hidden">
                    <CardHeader className="bg-secondary/20 border-b pb-4">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Terminal className="w-5 h-5 text-primary" />
                            Run History
                        </CardTitle>
                        <CardDescription>Records of recent automation activities.</CardDescription>
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
                                <XCircle className="w-12 h-12 text-destructive mx-auto" />
                                <h3 className="font-bold text-xl">Connection Error</h3>
                                <p className="text-muted-foreground">Unable to fetch execution logs.</p>
                            </div>
                        ) : !history || history.length === 0 ? (
                            <div className="p-20 text-center space-y-6">
                                <div className="bg-secondary p-6 rounded-full inline-block">
                                    <PlayCircle className="w-12 h-12 text-muted-foreground" />
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-2xl font-bold">No History Found</h3>
                                    <p className="text-muted-foreground max-w-sm mx-auto">
                                        Run an automation to see your logs appear here.
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader className="bg-secondary/10">
                                    <TableRow className="hover:bg-transparent border-border/40">
                                        <TableHead className="w-10"></TableHead>
                                        <TableHead className="font-bold text-xs uppercase py-4">Status</TableHead>
                                        <TableHead className="font-bold text-xs uppercase py-4">Automation</TableHead>
                                        <TableHead className="font-bold text-xs uppercase py-4">Executed At</TableHead>
                                        <TableHead className="font-bold text-xs uppercase py-4 text-right">Details</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {history.map((log) => (
                                        <>
                                            <TableRow
                                                key={log.id}
                                                className="group border-border/40 hover:bg-secondary/10 transition-colors cursor-pointer"
                                                onClick={() => toggleRow(log.id)}
                                            >
                                                <TableCell className="text-center pl-4">
                                                    {getStatusIcon(log.status)}
                                                </TableCell>
                                                <TableCell>{getStatusBadge(log.status)}</TableCell>
                                                <TableCell className="font-medium">{log.automation_name}</TableCell>
                                                <TableCell className="text-muted-foreground text-sm">
                                                    {new Date(log.created_at).toLocaleString()}
                                                </TableCell>
                                                <TableCell className="text-right pr-6">
                                                    {expandedRows.has(log.id) ? <ChevronUp className="w-4 h-4 inline" /> : <ChevronDown className="w-4 h-4 inline" />}
                                                </TableCell>
                                            </TableRow>
                                            {expandedRows.has(log.id) && (
                                                <TableRow className="bg-secondary/5 border-border/40">
                                                    <TableCell colSpan={5} className="p-6">
                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                            <div className="space-y-3">
                                                                <h4 className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-2">
                                                                    <Info className="w-3 h-3" /> Input Arguments
                                                                </h4>
                                                                <pre className="text-[11px] bg-background/50 p-4 rounded-xl border font-mono overflow-auto max-h-40">
                                                                    {JSON.stringify(log.input, null, 2)}
                                                                </pre>
                                                            </div>
                                                            <div className="space-y-3">
                                                                <h4 className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-2">
                                                                    <Terminal className="w-3 h-3" /> System Output
                                                                </h4>
                                                                <div className="space-y-2">
                                                                    {log.message && (
                                                                        <div className="text-xs text-destructive bg-destructive/5 p-2 rounded border border-destructive/10">
                                                                            {log.message}
                                                                        </div>
                                                                    )}
                                                                    {log.stdout && (
                                                                        <div>
                                                                            <span className="text-[10px] text-muted-foreground ml-1">STDOUT</span>
                                                                            <pre className="text-[11px] bg-background/50 p-4 rounded-xl border font-mono overflow-auto max-h-40">
                                                                                {log.stdout}
                                                                            </pre>
                                                                        </div>
                                                                    )}
                                                                    {log.stderr && (
                                                                        <div>
                                                                            <span className="text-[10px] text-destructive ml-1">STDERR</span>
                                                                            <pre className="text-[11px] bg-destructive/5 p-4 rounded-xl border border-destructive/10 font-mono overflow-auto max-h-40 text-destructive">
                                                                                {log.stderr}
                                                                            </pre>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                </TableRow>
                                            )}
                                        </>
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

export default Executions;
