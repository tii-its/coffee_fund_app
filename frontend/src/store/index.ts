import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/api/types'

interface AppState {
  // Current user selection (for kiosk mode)
  selectedUser: User | null
  setSelectedUser: (user: User | null) => void
  
  // Language
  language: 'en' | 'de'
  setLanguage: (language: 'en' | 'de') => void
  
  // Theme/UI state
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  
  // Current "logged in" user (for actions that require a user ID)
  currentUser: User | null
  setCurrentUser: (user: User | null) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      selectedUser: null,
      setSelectedUser: (user) => set({ selectedUser: user }),
      
      language: 'de', // Default to German as specified
      setLanguage: (language) => set({ language }),
      
      sidebarOpen: true,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      currentUser: null,
      setCurrentUser: (user) => set({ currentUser: user }),
    }),
    {
      name: 'coffee-fund-store',
      partialize: (state) => ({
        language: state.language,
        sidebarOpen: state.sidebarOpen,
        currentUser: state.currentUser,
      }),
    }
  )
)