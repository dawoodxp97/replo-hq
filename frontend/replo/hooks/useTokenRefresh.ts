"use client";

import { useEffect, useRef } from "react";
import Cookies from "js-cookie";
import { refreshToken } from "@/services/authService";
import { useGlobalStore } from "@/store/useGlobalStore";

/**
 * Hook to automatically refresh tokens before they expire
 * - Checks token expiration every 5 minutes
 * - Refreshes access token if it expires within 1 hour
 * - Refreshes refresh token if it expires within 12 hours
 */
export function useTokenRefresh() {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const refreshTokens = useGlobalStore((state: any) => state.refreshTokens);
  const isAuthenticated = useGlobalStore((state: any) => state.isAuthenticated);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    const checkAndRefreshTokens = async () => {
      const accessToken = Cookies.get("auth_token");
      const refreshTokenValue = Cookies.get("refresh_token");

      if (!accessToken || !refreshTokenValue) {
        return;
      }

      try {
        // Decode tokens to check expiration
        const decodeToken = (token: string): { exp?: number } | null => {
          try {
            const base64Url = token.split(".")[1];
            if (!base64Url) return null;
            const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
            const jsonPayload = decodeURIComponent(
              atob(base64)
                .split("")
                .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
                .join("")
            );
            return JSON.parse(jsonPayload);
          } catch {
            return null;
          }
        };

        const accessPayload = decodeToken(accessToken);
        const refreshPayload = decodeToken(refreshTokenValue);

        if (!accessPayload || !refreshPayload) {
          return;
        }

        const nowInSeconds = Math.floor(Date.now() / 1000);
        const oneHourInSeconds = 60 * 60; // 1 hour
        const twelveHoursInSeconds = 12 * 60 * 60; // 12 hours

        // Check if access token expires within 1 hour
        const accessExpiresSoon =
          accessPayload.exp &&
          accessPayload.exp - nowInSeconds < oneHourInSeconds;

        // Check if refresh token expires within 12 hours (refresh daily means refresh before it expires)
        const refreshExpiresSoon =
          refreshPayload.exp &&
          refreshPayload.exp - nowInSeconds < twelveHoursInSeconds;

        // Refresh if either token is about to expire
        if (accessExpiresSoon || refreshExpiresSoon) {
          try {
            const response = await refreshToken(refreshTokenValue);
            refreshTokens(response.access_token, response.refresh_token);
            console.log("Tokens refreshed automatically");
          } catch (error) {
            console.error("Failed to refresh tokens:", error);
            // If refresh fails, the apiClient will handle logout on next request
          }
        }
      } catch (error) {
        console.error("Error checking token expiration:", error);
      }
    };

    // Check immediately on mount
    checkAndRefreshTokens();

    // Then check every 5 minutes
    intervalRef.current = setInterval(checkAndRefreshTokens, 5 * 60 * 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isAuthenticated, refreshTokens]);
}

