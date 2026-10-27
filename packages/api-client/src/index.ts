import { createClient } from 'fetch-wrapper';

const apiClient = createClient({
  baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

export { apiClient };

// Placeholder - will be replaced when generated from OpenAPI
export interface Tutorial {}
export interface Repository {}
