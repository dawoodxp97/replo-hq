// ./frontend/src/lib/apiClient.js

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { BASE_URL } from "@/constants/apiEndpoints";
import { useGlobalStore } from "@/store/useGlobalStore";

// 1. Create the axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});
apiClient.interceptors.request.use(
  (config) => {
    // 1. Get state from Zustand
    const { token } = useGlobalStore.getState() as { token?: string }; 
    
    // 2. If token exists (from login OR refresh), add it
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  // ... (error handler)
);

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 3. This part is now CRITICAL
    if (error.response && error.response.status === 401) {
      // Token is invalid or expired
      const { logout } = useGlobalStore.getState() as { logout: () => void };
      logout(); // This clears the persisted state
      
      if (typeof window !== "undefined") {
        window.location.href = "/login"; // Redirect to login
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;