"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Search,
  BarChart3,
  BookOpen,
  History,
  CreditCard,
  Settings,
  HelpCircle,
  Activity
} from "lucide-react"
import { cn } from "@/lib/utils"
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
  SidebarFooter,
} from "@/components/ui/sidebar"
import { Progress } from "@/components/ui/progress"
import { currentUserPlan, plans } from "@/lib/mock-data"

const mainNavItems = [
  {
    title: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Nueva consulta",
    href: "/nueva-consulta",
    icon: Search,
  },
  {
    title: "Resultados",
    href: "/resultados",
    icon: BarChart3,
  },
  {
    title: "Storytelling",
    href: "/storytelling",
    icon: BookOpen,
  },
  {
    title: "Historial",
    href: "/historial",
    icon: History,
  },
]

const secondaryNavItems = [
  {
    title: "Membresia",
    href: "/membresia",
    icon: CreditCard,
  },
  {
    title: "Configuracion",
    href: "/configuracion",
    icon: Settings,
  },
  {
    title: "Ayuda",
    href: "/ayuda",
    icon: HelpCircle,
  },
]

export function AppSidebar() {
  const pathname = usePathname()
  const currentPlan = plans.find(p => p.id === currentUserPlan.planId)
  const usagePercent = (currentUserPlan.wordsUsed / currentUserPlan.wordsLimit) * 100

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-sidebar-border px-6 py-4">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Activity className="h-4 w-4 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-sidebar-foreground">Sentiment</span>
            <span className="text-xs text-muted-foreground">Social Analyzer</span>
          </div>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu principal</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNavItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === item.href}
                  >
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Cuenta</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {secondaryNavItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === item.href}
                  >
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border p-4">
        <div className="rounded-lg bg-sidebar-accent p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-sidebar-foreground">Plan {currentPlan?.name}</span>
            <span className="text-xs text-muted-foreground">{currentUserPlan.daysRemaining} dias restantes</span>
          </div>
          <Progress value={usagePercent} className="h-1.5 mb-2" />
          <p className="text-xs text-muted-foreground">
            {currentUserPlan.wordsUsed.toLocaleString()} / {currentUserPlan.wordsLimit.toLocaleString()} palabras
          </p>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
