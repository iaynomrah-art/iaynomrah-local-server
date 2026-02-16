import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";
import { ReactNode } from "react";
import { Separator } from "@/components/ui/separator";
import { ModeToggle } from "./ModeToggle";

interface LayoutProps {
    children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
    return (
        <SidebarProvider>
            <AppSidebar />
            <SidebarInset className="bg-background/95 backdrop-blur-xl">
                <header className="flex h-16 shrink-0 items-center justify-between px-6 border-b border-border/40 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12 bg-background/50 sticky top-0 z-20">
                    <div className="flex items-center gap-4">
                        <SidebarTrigger className="-ml-1 hover:bg-secondary transition-colors" />
                        <Separator orientation="vertical" className="mr-2 h-4" />
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-muted-foreground">Admin Panel</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <ModeToggle />
                    </div>
                </header>
                <div className="flex flex-1 flex-col p-4 md:p-8 overflow-y-auto">
                    {children}
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}
