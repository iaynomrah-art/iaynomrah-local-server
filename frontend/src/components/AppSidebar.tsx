import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarRail,
} from "@/components/ui/sidebar";
import { LayoutDashboard, Package, PlayCircle, Settings } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const items = [
    {
        title: "Dashboard",
        url: "/",
        icon: LayoutDashboard,
    },
    {
        title: "Automations",
        url: "/automations",
        icon: Package,
    },
    {
        title: "Executions",
        url: "/executions",
        icon: PlayCircle,
    },
];

export function AppSidebar() {
    const location = useLocation();

    return (
        <Sidebar collapsible="icon" className="border-r border-sidebar-border/50">
            <SidebarHeader className="h-16 flex items-center px-6 border-b border-sidebar-border/50">
                <div className="flex items-center gap-3">
                    <div className="bg-primary rounded-lg p-1.5 shadow-lg shadow-primary/20">
                        <Settings className="w-5 h-5 text-primary-foreground" />
                    </div>
                    <span className="font-bold text-xl tracking-tight group-data-[collapsible=icon]:hidden">
                        Harmony<span className="text-primary italic font-black">.</span>
                    </span>
                </div>
            </SidebarHeader>
            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel className="px-4 text-[10px] uppercase tracking-widest font-bold opacity-50 group-data-[collapsible=icon]:hidden">
                        Main Menu
                    </SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu className="px-2">
                            {items.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton
                                        asChild
                                        isActive={location.pathname === item.url}
                                        tooltip={item.title}
                                        className="h-11 rounded-xl transition-all duration-200 hover:bg-sidebar-accent/50 data-[active=true]:bg-primary/10 data-[active=true]:text-primary"
                                    >
                                        <Link to={item.url} className="flex items-center gap-3">
                                            <item.icon className={`w-5 h-5 ${location.pathname === item.url ? 'text-primary' : 'text-muted-foreground'}`} />
                                            <span className="font-semibold text-sm group-data-[collapsible=icon]:hidden">
                                                {item.title}
                                            </span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
            <SidebarRail />
        </Sidebar>
    );
}
