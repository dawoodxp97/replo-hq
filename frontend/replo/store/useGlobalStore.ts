import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import Cookies from 'js-cookie';

export interface AuthUser {
  id?: string;
  email?: string;
  username?: string;
  firstName?: string;
  lastName?: string;
  imageUrl?: string;
}

export interface GlobalState {
  // --- State ---
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isSidebarOpen: boolean;

  // --- Actions ---
  login: (userData: AuthUser, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  refreshTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (userData: AuthUser) => void;
  toggleSidebar: () => void;
}

export const useGlobalStore = create<GlobalState>()(
  persist(
    (set) => ({
      // --- State ---
      user: null,
      token: null,
      // We no longer need to store the token here, the cookie is the source of truth
      isAuthenticated: false,
      isSidebarOpen: false,

      // --- Actions ---
      login: (userData: AuthUser, accessToken: string, refreshToken: string) => {
        // Set both tokens in secure cookies
        Cookies.set('auth_token', accessToken, { 
          expires: 7, // Access token expires in 7 days (1 week)
          secure: process.env.NODE_ENV === 'production', // Only send over HTTPS in production
          sameSite: 'strict'
        });
        Cookies.set('refresh_token', refreshToken, { 
          expires: 1, // Refresh token expires in 1 day (refresh daily)
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'strict'
        });
        set({
          user: userData,
          isAuthenticated: true,
        });
      },

      logout: () => {
        // Remove both tokens
        Cookies.remove('auth_token');
        Cookies.remove('refresh_token');
        set({
          user: null,
          isAuthenticated: false,
        });
      },

      refreshTokens: (accessToken: string, refreshToken: string) => {
        // Update both tokens in cookies
        Cookies.set('auth_token', accessToken, { 
          expires: 7,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'strict'
        });
        Cookies.set('refresh_token', refreshToken, { 
          expires: 1,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'strict'
        });
      },

      setUser: (userData: AuthUser) => {
        set({
          user: userData,
          isAuthenticated: true,
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
      },

      toggleSidebar: () => {
        set((state) => ({ isSidebarOpen: !state.isSidebarOpen }));
      }
    }),
    {
      name: 'user-storage', // Persist the 'user' object and 'isAuthenticated' flag
      partialize: (state) => ({ user: (state as GlobalState).user, isAuthenticated: (state as GlobalState).isAuthenticated }),
    }
  )
);