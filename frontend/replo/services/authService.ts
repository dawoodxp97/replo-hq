import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
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
 * Expects JSON body per UserCreate schema (first_name, last_name, email, password).
 */
export const signup = (first_name: string, last_name: string, email: string, password: string) => {
  return apiClient.post(API_ENDPOINTS.USER_SIGNUP, { first_name, last_name, email, password });
};

/**
 * Refreshes access token using refresh token.
 */
export const refreshToken = (refreshToken: string): Promise<LoginResponse> => {
  return apiClient
    .post<LoginResponse>(API_ENDPOINTS.USER_REFRESH, { refresh_token: refreshToken })
    .then((data) => data as unknown as LoginResponse);
};
