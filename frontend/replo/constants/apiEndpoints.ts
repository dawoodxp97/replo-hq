export const BASE_URL = "http://localhost:8000";

export const API_ENDPOINTS = {
  // Health
  HEALTH: "/api/health",

  // Repository
  REPO_ANALYZE: "/api/repo",
  REPO_GET_ALL: "/api/repo",
  REPO_GET_BY_ID: (id: string) => `/api/repo/${id}`,

  // Tutorial
  TUTORIAL_GET_BY_ID: (id: string) => `/api/tutorial/${id}`,
  TUTORIAL_GET_ALL: "/api/tutorial",

  // User
  USER_LOGIN: "/api/user/login",
  USER_SIGNUP: "/api/user/signup",
  USER_ME: "/api/user/me",

  // Progress
  PROGRESS_COMPLETE_MODULE: "/api/progress/complete_module",
  PROGRESS_SUBMIT_QUIZ: "/api/progress/submit_quiz",
  PROGRESS_GET: "/api/progress",

  // Authoring
  AUTHOR_DASHBOARD: "/api/author",
  AUTHOR_UPDATE_MODULE: (id: string) => `/api/author/modules/${id}`,
  AUTHOR_UPDATE_QUIZ: (id: string) => `/api/author/quizzes/${id}`,
};