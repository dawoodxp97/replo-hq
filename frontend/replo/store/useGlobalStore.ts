// ./frontend/src/store/useGlobalStore.js
import { create } from 'zustand';

export interface AuthUser {
  id?: string;
  username?: string;
  token?: string;
}

export interface GlobalState {
  // --- 1. State ---
  user: AuthUser | null;
  isAuthenticated: boolean;
  isSidebarOpen: boolean;

  // --- 2. Actions ---
  login: (userData: AuthUser) => void;
  logout: () => void;
  toggleSidebar: () => void;
}

export const useGlobalStore = create<GlobalState>((set) => ({
  // --- 1. State ---

  // Auth State
  user: null,
  isAuthenticated: false,

  // UI State
  isSidebarOpen: true,

  // --- 2. Actions ---

  // Auth Actions
  login: (userData) => set({ user: userData, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),

  // UI Actions
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
}));