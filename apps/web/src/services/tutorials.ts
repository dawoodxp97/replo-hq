/**
 * Tutorial + generation service. Owns the SSE lifecycle (connect, heartbeats
 * are server-sent, disconnect on abort) behind a promise-based subscription.
 */
import {
  deleteTutorialApiTutorialTutorialIdDelete,
  exploreTutorialsApiTutorialExploreGet,
  generateTutorialApiTutorialGeneratePost,
  getGenerationStatusApiTutorialInstanceIdStatusGet,
  getGenerationResultApiTutorialInstanceIdResultGet,
  getTutorialApiTutorialTutorialIdGet,
  getTutorialBySlugApiTutorialSlugSlugGet,
  listTutorialsApiTutorialGet,
  retryGenerationApiTutorialInstanceIdRetryPost,
  setVisibilityApiTutorialTutorialIdVisibilityPatch,
} from '@replo/api-client';
import type {
  ExploreTutorialItem,
  GenerateRequest,
  GenerateResponse,
  Page_ExploreTutorialItem_,
  Page_TutorialListItem_,
  StatusResponse,
  TutorialListItem,
  TutorialResponse,
  VisibilityUpdate,
} from '@replo/api-client';
import { API_BASE_URL, toApiError } from '@/lib/api';

function assertData<T>(data: T | undefined, error: unknown, response?: Response): T {
  if (error !== undefined && error !== null) throw toApiError(error, response?.status ?? 0);
  return data as T;
}

export async function generate(request: GenerateRequest): Promise<GenerateResponse> {
  const { data, error, response } = await generateTutorialApiTutorialGeneratePost({ body: request });
  return assertData(data, error, response);
}

export async function status(instanceId: string): Promise<StatusResponse> {
  const { data, error, response } = await getGenerationStatusApiTutorialInstanceIdStatusGet({
    path: { instance_id: instanceId },
  });
  return assertData(data, error, response);
}

export async function retry(instanceId: string): Promise<GenerateResponse> {
  const { data, error, response } = await retryGenerationApiTutorialInstanceIdRetryPost({
    path: { instance_id: instanceId },
  });
  return assertData(data, error, response);
}

export async function library(params?: { limit?: number; offset?: number }): Promise<Page_TutorialListItem_> {
  const { data, error, response } = await listTutorialsApiTutorialGet({ query: params });
  return assertData(data, error, response);
}

export async function explore(params?: { language?: string | null; limit?: number; offset?: number }): Promise<Page_ExploreTutorialItem_> {
  const { data, error, response } = await exploreTutorialsApiTutorialExploreGet({ query: params });
  return assertData(data, error, response);
}

export async function get(tutorialId: string): Promise<TutorialResponse> {
  const { data, error, response } = await getTutorialApiTutorialTutorialIdGet({ path: { tutorial_id: tutorialId } });
  return assertData(data, error, response);
}

export async function bySlug(slug: string): Promise<TutorialResponse> {
  const { data, error, response } = await getTutorialBySlugApiTutorialSlugSlugGet({ path: { slug } });
  return assertData(data, error, response);
}

export async function remove(tutorialId: string): Promise<void> {
  const { error, response } = await deleteTutorialApiTutorialTutorialIdDelete({ path: { tutorial_id: tutorialId } });
  if (error) throw toApiError(error, response?.status);
}

export async function setVisibility(tutorialId: string, visibility: VisibilityUpdate['visibility']): Promise<TutorialResponse> {
  const { data, error, response } = await setVisibilityApiTutorialTutorialIdVisibilityPatch({
    path: { tutorial_id: tutorialId },
    body: { visibility },
  });
  return assertData(data, error, response);
}

export type GenerationEvent =
  | { type: 'status'; payload: StatusResponse }
  | { type: 'done'; payload: { status: 'completed' | 'failed' } }
  | { type: 'error'; message: string };

export type Unsubscribe = () => void;

/**
 * Subscribe to the generation stream. The stream authenticates with the
 * short-lived ticket from StatusResponse.stream_ticket (EventSource cannot
 * send headers). The returned unsubscribe closes the connection for good —
 * cleanup is the caller's one obligation.
 */
export function streamGeneration(
  instanceId: string,
  onEvent: (event: GenerationEvent) => void,
): Unsubscribe {
  let source: EventSource | null = null;
  let closed = false;
  let ticket: string | null = null;

  const open = (t: string) => {
    const url = `${API_BASE_URL}/api/tutorial/${instanceId}/stream?ticket=${encodeURIComponent(t)}`;
    source = new EventSource(url, { withCredentials: false });
    source.onmessage = (e) => {
      if (closed) return;
      try {
        const payload = JSON.parse(e.data) as StatusResponse;
        onEvent({ type: 'status', payload });
        if (payload.status === 'completed' || payload.status === 'failed') {
          closed = true;
          source?.close();
          source = null;
          onEvent({ type: 'done', payload: { status: payload.status } });
        }
      } catch {
        /* malformed frame: ignore, heartbeats will follow */
      }
    };
    source.onerror = () => {
      if (closed) return;
      source?.close();
      source = null;
      // Ticket may have expired; refresh it once from the polling endpoint.
      void status(instanceId)
        .then((s) => {
          if (closed) return;
          if (s.status === 'completed' || s.status === 'failed') {
            onEvent({ type: 'status', payload: s });
            closed = true;
            onEvent({ type: 'done', payload: { status: s.status } });
            return;
          }
          if (s.stream_ticket && s.stream_ticket !== ticket) {
            ticket = s.stream_ticket;
            open(s.stream_ticket);
          } else {
            onEvent({ type: 'error', message: 'Stream unavailable' });
          }
        })
        .catch((err: unknown) => onEvent({ type: 'error', message: toApiError(err).message }));
    };
  };

  void status(instanceId)
    .then((s) => {
      if (closed) return;
      onEvent({ type: 'status', payload: s });
      if (s.status === 'completed' || s.status === 'failed') {
        closed = true;
        onEvent({ type: 'done', payload: { status: s.status } });
        return;
      }
      ticket = s.stream_ticket;
      if (ticket) open(ticket);
    })
    .catch((err: unknown) => onEvent({ type: 'error', message: toApiError(err).message }));

  return () => {
    closed = true;
    source?.close();
    source = null;
  };
}

export async function rawResult(instanceId: string): Promise<unknown> {
  const { data, error, response } = await getGenerationResultApiTutorialInstanceIdResultGet({
    path: { instance_id: instanceId },
  });
  return assertData(data, error, response);
}

export type { TutorialListItem, ExploreTutorialItem, GenerateRequest, StatusResponse, TutorialResponse };
