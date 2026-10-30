/** Progress + quiz service. */
import {
  getProgressOverviewApiProgressGet,
  listModuleProgressApiProgressModulesGet,
  markModuleCompleteApiProgressCompleteModulePost,
  submitQuizAnswerApiProgressSubmitQuizPost,
  unmarkModuleCompleteApiProgressModulesModuleIdDelete,
} from '@replo/api-client';
import type {
  ModuleProgressDetail,
  Page_ModuleProgressDetail_,
  ProgressOverview,
  ProgressResponse,
  QuizResult,
  QuizSubmit,
} from '@replo/api-client';
import { toApiError } from '@/lib/api';

function assertData<T>(data: T | undefined, error: unknown, response?: Response): T {
  if (error !== undefined && error !== null) throw toApiError(error, response?.status ?? 0);
  return data as T;
}

export async function completeModule(moduleId: string): Promise<ProgressResponse> {
  const { data, error, response } = await markModuleCompleteApiProgressCompleteModulePost({ body: { module_id: moduleId } });
  return assertData(data, error, response);
}

export async function uncompleteModule(moduleId: string): Promise<void> {
  const { error, response } = await unmarkModuleCompleteApiProgressModulesModuleIdDelete({ path: { module_id: moduleId } });
  if (error) throw toApiError(error, response?.status);
}

export async function submitQuiz(submission: QuizSubmit): Promise<QuizResult> {
  const { data, error, response } = await submitQuizAnswerApiProgressSubmitQuizPost({ body: submission });
  return assertData(data, error, response);
}

export async function overview(): Promise<ProgressOverview> {
  const { data, error, response } = await getProgressOverviewApiProgressGet();
  return assertData(data, error, response);
}

export async function moduleHistory(params?: { limit?: number; offset?: number }): Promise<Page_ModuleProgressDetail_> {
  const { data, error, response } = await listModuleProgressApiProgressModulesGet({ query: params });
  return assertData(data, error, response);
}

export type { ModuleProgressDetail, QuizResult, QuizSubmit };
