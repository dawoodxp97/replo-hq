export const BASE_URL = "http://localhost:8000/api";

export const API_ENDPOINTS = {
  // Health
  HEALTH: "/health",

  // Repository
  REPO_ANALYZE: "/repo",
  REPO_GET_ALL: "/repo",
  REPO_GET_BY_ID: (id: string) => `/repo/${id}`,

  // Tutorial
  TUTORIAL_GET_BY_ID: (id: string) => `/tutorial/${id}`,
  TUTORIAL_GET_ALL: "/tutorial",

  // User
  USER_LOGIN: "/user/login",
  USER_SIGNUP: "/user/signup",
  USER_ME: "/user/me",

  // Progress
  PROGRESS_COMPLETE_MODULE: "/progress/complete_module",
  PROGRESS_SUBMIT_QUIZ: "/progress/submit_quiz",
  PROGRESS_GET: "/progress",

  // Authoring
  AUTHOR_DASHBOARD: "/author",
  AUTHOR_UPDATE_MODULE: (id: string) => `/author/modules/${id}`,
  AUTHOR_UPDATE_QUIZ: (id: string) => `/author/quizzes/${id}`,
};