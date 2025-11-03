
import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";

/**
 * Submits a GitHub URL for analysis.
 * @param {string} githubUrl - The URL of the GitHub repository.
 * @returns {Promise<object>} The analysis job details.
 */
export const analyzeRepo = (githubUrl: string) => {
  return apiClient.post(API_ENDPOINTS.REPO_ANALYZE, { github_url: githubUrl });
};

/**
 * Fetches a single tutorial by its ID.
 * @param {number} tutorialId - The ID of the tutorial.
 * @returns {Promise<object>} The tutorial data.
 */
export const getTutorialById = (tutorialId: string) => {
  return apiClient.get(API_ENDPOINTS.TUTORIAL_GET_BY_ID(tutorialId));
};

export interface GenerateTutorialRequest {
  repoUrl: string;
  difficulty: string;
  focus?: string[];
  description?: string;
}

export interface GenerationStatus {
  isGenerating: boolean;
  generationStep: number;
  generationProgress: number;
  generationId?: string;
  repoId?: string;
}

/**
 * Initiates tutorial generation for a repository.
 * @param {GenerateTutorialRequest} data - The generation request data.
 * @returns {Promise<object>} The generation job details.
 */
export const generateTutorial = (data: GenerateTutorialRequest) => {
  return apiClient.post(API_ENDPOINTS.TUTORIAL_GENERATE, data);
};

/**
 * Gets the status of an ongoing tutorial generation.
 * @param {string} repoUrl - The repository URL to check status for.
 * @returns {Promise<GenerationStatus>} The generation status.
 */
export const getGenerationStatus = (repoUrl: string): Promise<GenerationStatus> => {
  return apiClient.get(API_ENDPOINTS.TUTORIAL_GENERATION_STATUS, {
    params: { repo_url: repoUrl },
  });
};

// You can add all other tutorial-related API calls here:
// export const getAllTutorials = () => { ... }
// export const updateUserProgress = (tutorialId, progress) => { ... }