export interface Workspace {
  id: string
  name: string
  description?: string
  createdAt: string
}

export interface NavItem {
  id: string
  label: string
  icon: string
  href: string
}

export interface Message {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  createdAt: string
}

export interface Conversation {
  id: string
  title: string
  workspaceId: string
  messages: Message[]
  createdAt: string
}

export interface KnowledgeBase {
  id: string
  name: string
  workspaceId: string
  documentCount: number
  createdAt: string
}
