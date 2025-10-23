// ./frontend/src/lib/apiClient.js

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { BASE_URL, API_ENDPOINTS } from "@/constants/apiEndpoints";
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
  (error: AxiosError) => {
    // 3. Handle 401s without redirecting on /login or for login/signup requests
    if (error.response && error.response.status === 401) {
      const requestUrl = (error.config?.url || "").toString();
      const isAuthEndpoint =
        requestUrl.includes(API_ENDPOINTS.USER_LOGIN) ||
        requestUrl.includes(API_ENDPOINTS.USER_SIGNUP);

      const isOnLoginPage =
        typeof window !== "undefined" &&
        window.location.pathname.startsWith("/login");

      // Only force logout+redirect for protected requests
      if (!isAuthEndpoint && !isOnLoginPage) {
        const { logout } = useGlobalStore.getState() as { logout: () => void };
        logout(); // Clear any persisted auth state

        if (typeof window !== "undefined") {
          window.location.href = "/login"; // Redirect to login
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;