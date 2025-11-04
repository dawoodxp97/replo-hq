import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";

export interface EntityValue {
  id: string;
  label: string;
  type: 'repository' | 'tutorial' | 'module' | 'quiz';
  avatar?: string;
  tutorial_id?: string;
  module_index?: number;
}

export const searchEntities = async (query: string): Promise<EntityValue[]> => {
  const response = await apiClient.get(API_ENDPOINTS.SEARCH_ENTITIES, { params: { query } });
  return response as unknown as EntityValue[];
};