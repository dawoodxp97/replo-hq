import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";


export const getUserProfileSettings = () => {
  return apiClient.get(API_ENDPOINTS.SETTINGS_PROFILE);
};

