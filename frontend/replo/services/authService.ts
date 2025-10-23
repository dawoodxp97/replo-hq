// ./frontend/src/services/authService.js
import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";

/**
 * Logs in a user.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<object>} { token: { access_token, ... }, user: { id, email } }
 */
export const login = (email: string, password: string) => {
  return apiClient.post(API_ENDPOINTS.USER_LOGIN, { email, password });
};

/**
 * Registers a new user.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<object>} { id, email }
 */
export const signup = (email: string, password: string) => {
  return apiClient.post(API_ENDPOINTS.USER_SIGNUP, { email, password });
};