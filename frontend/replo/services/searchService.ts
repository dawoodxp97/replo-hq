import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";

interface EntityValue {
  label: string;
  value: string;
  id: string;
  avatar?: string;
  type: 'repository' | 'tutorial' | 'module' | 'quiz';
}

export const searchEntities = async (query: string): Promise<EntityValue[]> => {
  const response = await apiClient.get(API_ENDPOINTS.SEARCH_ENTITIES, { params: { query } });
  return response.data as unknown as EntityValue[];
};