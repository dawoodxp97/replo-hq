// ./frontend/src/lib/apiClient.js

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { BASE_URL, API_ENDPOINTS } from "@/constants/apiEndpoints";
import { useGlobalStore } from "@/store/useGlobalStore";
import Cookies from "js-cookie";

// 1. Create the axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});
apiClient.interceptors.request.use(
  (config) => {
    // Prefer cookie-based token for requests
    const token = typeof window !== "undefined" ? Cookies.get("auth_token") : undefined;
    if (token) {
      (config.headers as any)["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  // ... (error handler)
);

apiClient.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError) => {
    // Handle 401s without redirecting on /login or for login/signup requests
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
        logout(); // Clear any persisted auth state and cookie

        if (typeof window !== "undefined") {
          window.location.href = "/login?error=expired"; // Redirect with expired flag
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;