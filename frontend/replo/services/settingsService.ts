import apiClient from "@/lib/apiClient";
import { API_ENDPOINTS } from "@/constants/apiEndpoints";


export type ProfileSettingsResponse = {
  first_name: string | null;
  last_name: string | null;
  email: string;
  bio: string | null;
  location: string | null;
  website: string | null;
  profile_picture_url: string | null;
  connected_accounts: ConnectedAccount[];
};

export type ConnectedAccount = {
  id: number;
  name: string;
  connected: boolean;
  username: string;
};

export type NotificationSettingsResponse = {
  email_notifications_enabled: boolean;
  tutorial_completions: boolean;
  new_features: boolean;
  weekly_digest: boolean;
  browser_notifications: boolean;
};

export type AppearanceSettingsResponse = {
  language: string;
  code_editor_theme: string;
};

export type LearningSettingsResponse = {
  default_difficulty_level: string;
  daily_learning_goal: number;
  auto_play_next_module: boolean;
  show_code_hints: boolean;
  quiz_mode: boolean;
};

export type SecuritySettingsResponse = {
  delete_account: boolean;
};

export const getUserProfileSettings = async (): Promise<ProfileSettingsResponse> => {
  const response = await apiClient.get<ProfileSettingsResponse>(API_ENDPOINTS.SETTINGS_PROFILE);
  return response as unknown as ProfileSettingsResponse;
};

export const updateUserProfileSettings = async (profileSettings: ProfileSettingsResponse): Promise<ProfileSettingsResponse> => {
  const response = await apiClient.put<ProfileSettingsResponse>(API_ENDPOINTS.SETTINGS_PROFILE, profileSettings);
  return response as unknown as ProfileSettingsResponse;
};

export const getUserNotificationSettings = async (): Promise<NotificationSettingsResponse> => {
  const response = await apiClient.get<NotificationSettingsResponse>(API_ENDPOINTS.SETTINGS_NOTIFICATIONS);
  return response as unknown as NotificationSettingsResponse;
};

export const updateUserNotificationSettings = async (notificationSettings: NotificationSettingsResponse): Promise<NotificationSettingsResponse> => {
  const response = await apiClient.put<NotificationSettingsResponse>(API_ENDPOINTS.SETTINGS_NOTIFICATIONS, notificationSettings);
  return response as unknown as NotificationSettingsResponse;
};

export const getUserAppearanceSettings = async (): Promise<AppearanceSettingsResponse> => {
  const response = await apiClient.get<AppearanceSettingsResponse>(API_ENDPOINTS.SETTINGS_APPEARANCE);
  return response as unknown as AppearanceSettingsResponse;
};

export const updateUserAppearanceSettings = async (appearanceSettings: AppearanceSettingsResponse): Promise<AppearanceSettingsResponse> => {
  const response = await apiClient.put<AppearanceSettingsResponse>(API_ENDPOINTS.SETTINGS_APPEARANCE, appearanceSettings);
  return response as unknown as AppearanceSettingsResponse;
};

export const getUserLearningSettings = async (): Promise<LearningSettingsResponse> => {
  const response = await apiClient.get<LearningSettingsResponse>(API_ENDPOINTS.SETTINGS_LEARNING);
  return response as unknown as LearningSettingsResponse;
};

export const updateUserLearningSettings = async (learningSettings: LearningSettingsResponse): Promise<LearningSettingsResponse> => {
  const response = await apiClient.put<LearningSettingsResponse>(API_ENDPOINTS.SETTINGS_LEARNING, learningSettings);
  return response as unknown as LearningSettingsResponse;
};

export const getUserSecuritySettings = async (): Promise<SecuritySettingsResponse> => {
  const response = await apiClient.get<SecuritySettingsResponse>(API_ENDPOINTS.SETTINGS_SECURITY);
  return response as unknown as SecuritySettingsResponse;
};

export const updateUserSecuritySettings = async (securitySettings: SecuritySettingsResponse): Promise<SecuritySettingsResponse> => {
  const response = await apiClient.put<SecuritySettingsResponse>(API_ENDPOINTS.SETTINGS_SECURITY, securitySettings);
  return response as unknown as SecuritySettingsResponse;
};