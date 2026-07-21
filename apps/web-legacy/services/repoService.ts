import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";

export interface Repository {
  repo_id: string;
  github_url: string;
  name: string | null;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface RepoListResponse {
  repositories: Repository[];
}

export interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileTreeNode[] | null;
}

export interface RepoFileTreeResponse {
  tree: FileTreeNode[];
}

export interface RepoFileContentResponse {
  content: string;
  path: string;
  size: number;
}

export interface RepoDetailResponse {
  repository: Repository;
  tutorials: Array<{
    tutorial_id: string;
    level: string;
    title: string;
  }>;
}

export const getRepositories = async (): Promise<RepoListResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.REPO_GET_ALL);
  return response as unknown as RepoListResponse;
};

export const getRepositoryById = async (repoId: string): Promise<RepoDetailResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.REPO_GET_BY_ID(repoId));
  return response as unknown as RepoDetailResponse;
};

export const getRepositoryFileTree = async (repoId: string): Promise<RepoFileTreeResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.REPO_GET_TREE(repoId));
  return response as unknown as RepoFileTreeResponse;
};

export const getRepositoryFileContent = async (
  repoId: string,
  filePath: string
): Promise<RepoFileContentResponse> => {
  const response = await apiClient.get(API_ENDPOINTS.REPO_GET_FILE(repoId), {
    params: { file_path: filePath },
  });
  return response as unknown as RepoFileContentResponse;
};

