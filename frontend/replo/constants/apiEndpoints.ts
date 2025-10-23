export const BASE_URL = "http://localhost:8000";


export const API_ENDPOINTS = {
  // Health
  HEALTH: "/health",

  // Repository
  REPO_ANALYZE: "/repo/analyze",

  // Tutorial
  TUTORIAL_GET_BY_ID: (id: number) => `/tutorial/${id}`,
  TUTORIAL_GET_ALL: "/tutorial/all", // Assuming you'll add this

  // User & Progress
  USER_LOGIN: "/api/user/login", // Assuming
  USER_SIGNUP: "/api/user/signup", // Assuming
  USER_PROGRESS: "/api/user/progress",

  // Authoring
  AUTHOR_UPDATE_TUTORIAL: (id: number) => `/api/author/tutorial/${id}`,
};