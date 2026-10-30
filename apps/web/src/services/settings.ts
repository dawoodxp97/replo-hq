/** Settings + BYOK credentials service. */
import {
  addCredentialApiSettingsCredentialsPost,
  changePasswordApiSettingsSecurityPasswordPut,
  deleteCredentialApiSettingsCredentialsCredentialIdDelete,
  getAllSettingsApiSettingsAllGet,
  listCredentialsApiSettingsCredentialsGet,
  revokeSessionsApiSettingsSecurityRevokeSessionsPost,
  updateAppearanceApiSettingsAppearancePatch,
  updateLearningApiSettingsLearningPatch,
  updateNotificationsApiSettingsNotificationsPatch,
  updateProfileApiSettingsProfilePatch,
} from '@replo/api-client';
import type {
  AppearanceSettingsUpdate,
  CredentialCreate,
  CredentialCreateResponse,
  CredentialResponse,
  LearningSettingsUpdate,
  NotificationSettingsUpdate,
  PasswordChangeRequest,
  ProfileSettingsUpdate,
  UserSettingsResponse,
} from '@replo/api-client';
import { toApiError } from '@/lib/api';

function assertData<T>(data: T | undefined, error: unknown, response?: Response): T {
  if (error !== undefined && error !== null) throw toApiError(error, response?.status ?? 0);
  return data as T;
}

export const all = async (): Promise<UserSettingsResponse> => {
  const { data, error, response } = await getAllSettingsApiSettingsAllGet();
  return assertData(data, error, response);
};
export const updateProfile = async (body: ProfileSettingsUpdate) => {
  const { data, error, response } = await updateProfileApiSettingsProfilePatch({ body });
  return assertData(data, error, response);
};
export const updateNotifications = async (body: NotificationSettingsUpdate) => {
  const { data, error, response } = await updateNotificationsApiSettingsNotificationsPatch({ body });
  return assertData(data, error, response);
};
export const updateAppearance = async (body: AppearanceSettingsUpdate) => {
  const { data, error, response } = await updateAppearanceApiSettingsAppearancePatch({ body });
  return assertData(data, error, response);
};
export const updateLearning = async (body: LearningSettingsUpdate) => {
  const { data, error, response } = await updateLearningApiSettingsLearningPatch({ body });
  return assertData(data, error, response);
};
export const changePassword = async (body: PasswordChangeRequest): Promise<void> => {
  const { error, response } = await changePasswordApiSettingsSecurityPasswordPut({ body });
  if (error) throw toApiError(error, response?.status);
};
export const revokeSessions = async (): Promise<void> => {
  const { error, response } = await revokeSessionsApiSettingsSecurityRevokeSessionsPost();
  if (error) throw toApiError(error, response?.status);
};
export const listCredentials = async (): Promise<CredentialResponse[]> => {
  const { data, error, response } = await listCredentialsApiSettingsCredentialsGet();
  return assertData(data, error, response);
};
export const addCredential = async (body: CredentialCreate): Promise<CredentialCreateResponse> => {
  const { data, error, response } = await addCredentialApiSettingsCredentialsPost({ body });
  return assertData(data, error, response);
};
export const deleteCredential = async (credentialId: string): Promise<void> => {
  const { error, response } = await deleteCredentialApiSettingsCredentialsCredentialIdDelete({ path: { credential_id: credentialId } });
  if (error) throw toApiError(error, response?.status);
};
