
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

// You can add all other tutorial-related API calls here:
// export const getAllTutorials = () => { ... }
// export const updateUserProgress = (tutorialId, progress) => { ... }