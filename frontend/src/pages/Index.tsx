import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useState, useEffect } from "react";
import PathInput from "@/components/modal/PathInput";
import { Layout } from "@/components/Layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Settings, FolderOpen, Cpu, AlertCircle, RefreshCw } from "lucide-react";
import heroImage from "@/assets/hero-image.jpg";

interface DashboardConfig {
  PUBLISH_AUTOMATION_FOLDER: string;
  UI_ROBOT_PATH: string;
  PUBLISH_AUTOMATION_FOLDER_STATUS: "hasValue" | "empty";
  UI_ROBOT_PATH_STATUS: "hasValue" | "empty";
}

const Index = () => {
  const [modalConfig, setModalConfig] = useState<{
    isOpen: boolean;
    title: string;
    description: string;
    envKey: "PUBLISH_AUTOMATION_FOLDER" | "UI_ROBOT_PATH";
    defaultValue: string;
  } | null>(null);

  const { data, isLoading, isError, refetch } = useQuery<DashboardConfig>({
    queryKey: ["dashboard-config"],
    queryFn: async () => {
      const response = await axios.get("/api/v1/dashboard/");
      return response.data;
    },
  });

  // Automatically open modal if values are missing
  useEffect(() => {
    if (data && !isLoading) {
      if (data.UI_ROBOT_PATH_STATUS === "empty" && !modalConfig?.isOpen) {
        handleOpenModal("UI_ROBOT_PATH");
      } else if (data.PUBLISH_AUTOMATION_FOLDER_STATUS === "empty" && !modalConfig?.isOpen) {
        handleOpenModal("PUBLISH_AUTOMATION_FOLDER");
      }
    }
  }, [data, isLoading]);

  const handleOpenModal = (key: "PUBLISH_AUTOMATION_FOLDER" | "UI_ROBOT_PATH") => {
    if (key === "UI_ROBOT_PATH") {
      setModalConfig({
        isOpen: true,
        title: "UiRobot Path Configuration",
        description: "Specify the absolute path to your UiRobot.exe file.",
        envKey: "UI_ROBOT_PATH",
        defaultValue: data?.UI_ROBOT_PATH || ""
      });
    } else {
      setModalConfig({
        isOpen: true,
        title: "Publish Automation Folder",
        description: "Specify the local folder where your automation packages are published.",
        envKey: "PUBLISH_AUTOMATION_FOLDER",
        defaultValue: data?.PUBLISH_AUTOMATION_FOLDER || ""
      });
    }
  };

  return (
    <Layout>
      <main className="flex-1 flex flex-col items-center justify-center space-y-8 max-w-5xl mx-auto w-full">

        {/* Hero Section */}
        <div className="text-center space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="relative group max-w-md mx-auto rounded-2xl overflow-hidden shadow-2xl transition-transform hover:scale-[1.02]">
            <img
              src={heroImage}
              alt="Welcome illustration"
              className="w-full h-48 object-cover object-center"
            />
            <div className="absolute inset-0 bg-primary/10 group-hover:bg-transparent transition-colors" />
          </div>
          <div className="space-y-2">
            <h1 className="text-5xl font-extrabold text-foreground tracking-tight">
              Harmony <span className="text-primary italic">Server</span>
            </h1>
            <p className="text-muted-foreground text-lg max-w-lg mx-auto">
              Centralized orchestration for your UiPath automations and path configurations.
            </p>
          </div>
        </div>

        {/* Status Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
          {/* UiRobot Path Card */}
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">UiRobot Path</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : isError ? (
                <div className="flex items-center text-destructive text-sm gap-2">
                  <AlertCircle className="h-4 w-4" />
                  <span>Failed to load config</span>
                  <Button variant="ghost" size="sm" onClick={() => refetch()}>Retry</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Badge variant={data?.UI_ROBOT_PATH_STATUS === "hasValue" ? "default" : "destructive"}>
                      {data?.UI_ROBOT_PATH_STATUS === "hasValue" ? "Configured" : "Missing"}
                    </Badge>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded-md border border-border/50 font-mono text-xs break-all min-h-[40px]">
                    {data?.UI_ROBOT_PATH || "Not set - please configure"}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full flex gap-2"
                    onClick={() => handleOpenModal("UI_ROBOT_PATH")}
                  >
                    <Settings className="h-3 w-3" /> Update Path
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Publish Folder Card */}
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Publish Automation Folder</CardTitle>
              <FolderOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : isError ? (
                <div className="flex items-center text-destructive text-sm gap-2">
                  <AlertCircle className="h-4 w-4" />
                  <span>Failed to load config</span>
                  <Button variant="ghost" size="sm" onClick={() => refetch()}>Retry</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Badge variant={data?.PUBLISH_AUTOMATION_FOLDER_STATUS === "hasValue" ? "default" : "destructive"}>
                      {data?.PUBLISH_AUTOMATION_FOLDER_STATUS === "hasValue" ? "Configured" : "Missing"}
                    </Badge>
                  </div>
                  <div className="p-3 bg-secondary/50 rounded-md border border-border/50 font-mono text-xs break-all min-h-[40px]">
                    {data?.PUBLISH_AUTOMATION_FOLDER || "Not set - please configure"}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full flex gap-2"
                    onClick={() => handleOpenModal("PUBLISH_AUTOMATION_FOLDER")}
                  >
                    <Settings className="h-3 w-3" /> Update Folder
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Global Refresh */}
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Force Refresh Data
        </Button>
      </main>



      {/* Configuration Modal */}
      {modalConfig && (
        <PathInput
          isOpen={modalConfig.isOpen}
          onClose={() => setModalConfig(prev => prev ? { ...prev, isOpen: false } : null)}
          title={modalConfig.title}
          description={modalConfig.description}
          envKey={modalConfig.envKey}
          defaultValue={modalConfig.defaultValue}
        />
      )}
    </Layout>
  );
};

export default Index;
