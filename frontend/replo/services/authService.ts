// ./frontend/src/services/authService.js
import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: { id?: string; email?: string; username?: string };
};

/**
 * Logs in a user.
 * Backend expects OAuth2PasswordRequestForm (username, password) as form data.
 */
export const login = (email: string, password: string): Promise<LoginResponse> => {
  const params = new URLSearchParams();
  params.append("username", email);
  params.append("password", password);
  // apiClient returns response.data (runtime). Narrow type for TS.
  return apiClient
    .post<LoginResponse>(API_ENDPOINTS.USER_LOGIN, params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    })
    .then((data) => data as unknown as LoginResponse);
};

/**
 * Registers a new user.
 * Expects JSON body per UserCreate schema (email, password).
 */
export const signup = (email: string, password: string) => {
  return apiClient.post(API_ENDPOINTS.USER_SIGNUP, { email, password });
};
