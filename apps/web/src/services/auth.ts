/**
 * Auth service: the only caller of the auth endpoints. Failures surface as
 * ApiError carrying the backend's AppError code — never ad-hoc HTTP objects.
 */
import {
  getMeApiUserMeGet,
  loginApiUserLoginPost,
  oauthAuthorizeApiUserOauthProviderAuthorizeGet,
  oauthCallbackApiUserOauthProviderCallbackGet,
  signupApiUserSignupPost,
  urlSearchParamsBodySerializer,
} from '@replo/api-client';
import type {
  Body_login_api_user_login_post,
  OAuthProvider,
  TokenWithUser,
  UserCreate,
  UserPublic,
} from '@replo/api-client';
import { ApiError, toApiError } from '@/lib/api';

function assertData<T>(data: T | undefined, error: unknown, response?: Response): T {
  if (error !== undefined && error !== null) throw toApiError(error, response?.status ?? 0);
  return data as T;
}

export async function login(email: string, password: string): Promise<TokenWithUser> {
  const form: Body_login_api_user_login_post = { username: email, password };
  const { data, error, response } = await loginApiUserLoginPost({
    // OAuth2PasswordRequestForm is form-encoded, not JSON: serialize here and
    // send a string body with the matching content type.
    body: urlSearchParamsBodySerializer.bodySerializer(form),
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return assertData(data, error, response);
}

export async function signup(payload: UserCreate): Promise<UserPublic> {
  const { data, error, response } = await signupApiUserSignupPost({ body: payload });
  return assertData(data, error, response);
}

export async function me(): Promise<UserPublic> {
  const { data, error, response } = await getMeApiUserMeGet();
  return assertData(data, error, response);
}

/** Returns the provider's authorize URL; the SPA navigates the top window to it. */
export async function oauthAuthorizeUrl(provider: OAuthProvider): Promise<string> {
  const { data, error, response } = await oauthAuthorizeApiUserOauthProviderAuthorizeGet({ path: { provider } });
  const payload = assertData(data, error, response) as { authorize_url?: string; url?: string };
  const url = payload.authorize_url ?? payload.url;
  if (!url) throw new ApiError(0, 'Authorize endpoint returned no URL');
  return url;
}

/** Provider landed back on our origin with code+state; exchange for a session. */
export async function oauthComplete(
  provider: OAuthProvider,
  params: { code: string; state: string },
): Promise<TokenWithUser> {
  const { data, error, response } = await oauthCallbackApiUserOauthProviderCallbackGet({
    path: { provider },
    query: params,
  });
  return assertData(data, error, response);
}

export { ApiError };
