'use client'

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StoreChatInterface } from "@/components/store-chat-interface"
import { DashboardContent } from "@/components/dashboard-content" // Your existing dashboard

interface DashboardTabsProps {
  storeData: any // Replace with proper type
}

export function DashboardTabs({ storeData }: DashboardTabsProps) {
  return (
    <Tabs defaultValue="dashboard" className="flex-1">
      <TabsList>
        <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
        <TabsTrigger value="chat">AI Assistant</TabsTrigger>
      </TabsList>
      <TabsContent value="dashboard" className="flex-1">
        <DashboardContent storeData={storeData} />
      </TabsContent>
      <TabsContent value="chat" className="flex-1">
        <StoreChatInterface storeData={storeData} />
      </TabsContent>
    </Tabs>
  )
} 