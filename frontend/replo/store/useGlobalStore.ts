import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import Cookies from 'js-cookie';

export interface AuthUser {
  id?: string;
  email?: string;
  username?: string;
}

export interface GlobalState {
  // --- State ---
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isSidebarOpen: boolean;

  // --- Actions ---
  login: (userData: AuthUser, token: string) => void;
  logout: () => void;
  toggleSidebar: () => void;
}

export const useGlobalStore = create(
  persist(
    (set) => ({
      // --- State ---
      user: null,
      // We no longer need to store the token here, the cookie is the source of truth
      isAuthenticated: false,

      // --- Actions ---
      login: (userData: AuthUser, token: string) => {
        // 2. Set the token in a secure cookie
        Cookies.set('auth_token', token, { 
          expires: 1, // Expires in 1 day
          secure: process.env.NODE_ENV === 'production', // Only send over HTTPS in production
          sameSite: 'strict'
        });
        set({
          user: userData,
          isAuthenticated: true,
        });
      },

      logout: () => {
        // 3. Remove the cookie
        Cookies.remove('auth_token');
        set({
          user: null,
          isAuthenticated: false,
        });
      },

      // This action is new: it will be used to initialize the store on app load
      hydrateAuth: () => {
        const token = Cookies.get('auth_token');
        if (token) {
          // Here you might want to fetch the user data if it's not in the store
          // For now, we'll just set isAuthenticated
          set({ isAuthenticated: true });
        }
      }
    }),
    {
      name: 'user-storage', // Persist the 'user' object and 'isAuthenticated' flag
      partialize: (state) => ({ user: (state as GlobalState).user, isAuthenticated: (state as GlobalState).isAuthenticated }),
    }
  )
);