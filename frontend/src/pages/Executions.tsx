import { Layout } from "@/components/Layout";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PlayCircle } from "lucide-react";

const Executions = () => {
    return (
        <Layout>
            <div className="space-y-6 max-w-7xl mx-auto w-full">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Executions</h2>
                    <p className="text-muted-foreground mt-1">
                        Monitor and track your automation runs.
                    </p>
                </div>

                <Card className="border-dashed border-2 flex flex-col items-center justify-center p-12 text-center h-[400px]">
                    <div className="bg-secondary p-6 rounded-full mb-6">
                        <PlayCircle className="w-12 h-12 text-muted-foreground" />
                    </div>
                    <CardHeader>
                        <CardTitle>No Execution History</CardTitle>
                        <CardDescription>
                            Run an automation from the dashboard or via API to see logs here.
                        </CardDescription>
                    </CardHeader>
                </Card>
            </div>
        </Layout>
    );
};

export default Executions;
