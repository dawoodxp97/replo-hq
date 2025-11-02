// ./frontend/src/lib/apiClient.js

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { BASE_URL, API_ENDPOINTS } from "@/constants/apiEndpoints";
import { useGlobalStore } from "@/store/useGlobalStore";
import { refreshToken } from "@/services/authService";
import Cookies from "js-cookie";

// 1. Create the axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

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
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401s - attempt token refresh
    if (error.response && error.response.status === 401 && originalRequest && !originalRequest._retry) {
      const requestUrl = (originalRequest.url || "").toString();
      const isAuthEndpoint =
        requestUrl.includes(API_ENDPOINTS.USER_LOGIN) ||
        requestUrl.includes(API_ENDPOINTS.USER_SIGNUP) ||
        requestUrl.includes(API_ENDPOINTS.USER_REFRESH);

      const isOnLoginPage =
        typeof window !== "undefined" &&
        window.location.pathname.startsWith("/login");

      // Don't try to refresh for auth endpoints
      if (isAuthEndpoint) {
        return Promise.reject(error);
      }

      // If we're already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshTokenValue = typeof window !== "undefined" ? Cookies.get("refresh_token") : undefined;

      if (!refreshTokenValue) {
        // No refresh token, logout
        const { logout } = useGlobalStore.getState() as { logout: () => void };
        logout();
        processQueue(new Error("No refresh token"), null);
        isRefreshing = false;

        if (typeof window !== "undefined" && !isOnLoginPage) {
          window.location.href = "/login?error=expired";
        }
        return Promise.reject(error);
      }

      try {
        // Attempt to refresh tokens
        const response = await refreshToken(refreshTokenValue);
        
        // Update tokens in store and cookies
        const { refreshTokens } = useGlobalStore.getState() as { refreshTokens: (accessToken: string, refreshToken: string) => void };
        refreshTokens(response.access_token, response.refresh_token);

        // Update the original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
        }

        // Process queued requests
        processQueue(null, response.access_token);
        isRefreshing = false;

        // Retry the original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        processQueue(refreshError as Error, null);
        isRefreshing = false;

        const { logout } = useGlobalStore.getState() as { logout: () => void };
        logout();

        if (typeof window !== "undefined" && !isOnLoginPage) {
          window.location.href = "/login?error=expired";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;