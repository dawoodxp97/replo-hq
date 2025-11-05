export const BASE_URL = 
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const API_ENDPOINTS = {
  // Search
  SEARCH_ENTITIES: "/search/entities",

  // Health
  HEALTH: "/health",

  // Repository
  REPO_ANALYZE: "/repo",
  REPO_GET_ALL: "/repo",
  REPO_GET_BY_ID: (id: string) => `/repo/${id}`,
  REPO_GET_TREE: (id: string) => `/repo/${id}/tree`,
  REPO_GET_FILE: (id: string) => `/repo/${id}/file`,

  // Tutorial
  TUTORIAL_GET_BY_ID: (id: string) => `/tutorial/${id}`,
  TUTORIAL_GET_ALL: "/tutorial",
  TUTORIAL_GENERATE: "/tutorial/generate",
  TUTORIAL_GENERATION_STATUS: "/tutorial/generation/status",

  // User
  USER_LOGIN: "/user/login",
  USER_SIGNUP: "/user/signup",
  USER_ME: "/user/me",
  USER_REFRESH: "/user/refresh",

  // Progress
  PROGRESS_COMPLETE_MODULE: "/progress/complete_module",
  PROGRESS_SUBMIT_QUIZ: "/progress/submit_quiz",
  PROGRESS_GET: "/progress",

  // Authoring
  AUTHOR_DASHBOARD: "/author",
  AUTHOR_UPDATE_TUTORIAL: (id: string) => `/author/tutorials/${id}`,
  AUTHOR_UPDATE_MODULE: (id: string) => `/author/modules/${id}`,
  AUTHOR_UPDATE_QUIZ: (id: string) => `/author/quizzes/${id}`,
  AUTHOR_REORDER_MODULES: (id: string) => `/author/tutorials/${id}/modules/reorder`,


  // Settings
  SETTINGS_PROFILE: "/settings/profile",
  SETTINGS_NOTIFICATIONS: "/settings/notifications",
  SETTINGS_APPEARANCE: "/settings/appearance",
  SETTINGS_LEARNING: "/settings/learning",
  SETTINGS_SECURITY: "/settings/security",
  SETTINGS_SECURITY_PASSWORD: "/settings/security/password",
  SETTINGS_LLM: "/settings/llm",
  // Notifications
  NOTIFICATIONS_GET: "/notifications",
  NOTIFICATIONS_MARK_READ: (id: string) => `/notifications/${id}/read`,
  NOTIFICATIONS_MARK_ALL_READ: "/notifications/read-all",

  // Dashboard
  DASHBOARD_STATS: "/dashboard/stats",
  DASHBOARD_WEEKLY_ACTIVITY: "/dashboard/weekly-activity",
  DASHBOARD_TUTORIAL_STATUS: "/dashboard/tutorial-status",
  DASHBOARD_RECENT_ACTIVITY: "/dashboard/recent-activity",
};