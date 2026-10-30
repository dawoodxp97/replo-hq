/** Repository service. */
import { addRepositoryApiRepoPost, deleteRepositoryApiRepoRepoIdDelete, listRepositoriesApiRepoGet } from '@replo/api-client';
import type { Page_RepoResponse_, RepoCreate } from '@replo/api-client';
import { toApiError } from '@/lib/api';

function assertData<T>(data: T | undefined, error: unknown, response?: Response): T {
  if (error !== undefined && error !== null) throw toApiError(error, response?.status ?? 0);
  return data as T;
}

export async function add(body: RepoCreate) {
  const { data, error, response } = await addRepositoryApiRepoPost({ body });
  return assertData(data, error, response);
}
export async function list(params?: { limit?: number; offset?: number }) {
  const { data, error, response } = await listRepositoriesApiRepoGet({ query: params });
  return assertData(data, error, response) as Page_RepoResponse_;
}
export async function remove(repoId: string): Promise<void> {
  const { error, response } = await deleteRepositoryApiRepoRepoIdDelete({ path: { repo_id: repoId } });
  if (error) throw toApiError(error, response?.status);
}
