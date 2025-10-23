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

// 2. Request Interceptor (Middleware)
// This runs BEFORE any request is sent
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { isAuthenticated, user } = useGlobalStore.getState();

    if (isAuthenticated && user?.token) {
      config.headers = config.headers ?? {};
      (config.headers as Record<string, string>)["Authorization"] = `Bearer ${user.token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 3. Response Interceptor (Middleware)
// This runs AFTER a response is received
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error: AxiosError) => {
    const status = error.response?.status;

    if (status === 401) {
      const { logout } = useGlobalStore.getState();
      logout();

      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;