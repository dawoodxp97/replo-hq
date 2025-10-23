export const BASE_URL = "http://localhost:8000/api/v1";


export const API_ENDPOINTS = {
  // Health
  HEALTH: "/health",

  // Repository
  REPO_ANALYZE: "/repo/analyze",

  // Tutorial
  TUTORIAL_GET_BY_ID: (id: number) => `/tutorial/${id}`,
  TUTORIAL_GET_ALL: "/tutorial/all", // Assuming you'll add this

  // User & Progress
  USER_LOGIN: "/user/login", // Assuming
  USER_SIGNUP: "/user/signup", // Assuming
  USER_PROGRESS: "/user/progress",

  // Authoring
  AUTHOR_UPDATE_TUTORIAL: (id: number) => `/author/tutorial/${id}`,
};