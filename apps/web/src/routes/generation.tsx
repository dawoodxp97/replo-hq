import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from '@tanstack/react-router';
import { Button } from '@replo/ui';
import { retry, streamGeneration, type GenerationEvent, type Unsubscribe } from '@/services/tutorials';
import type { StatusResponse } from '@replo/api-client';
import { ErrorState, Loading } from '@/components/states';

/** Live generation status via SSE — no polling while the stream is healthy. */
export function GenerationPage() {
  const { instanceId = '' } = useParams({ from: '/generation/$instanceId' });
  const navigate = useNavigate();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [unsubscribe, setUnsubscribe] = useState<Unsubscribe | null>(null);

  useEffect(() => {
    const handle = (event: GenerationEvent) => {
      if (event.type === 'status') setStatus(event.payload);
      else if (event.type === 'error') setError(new Error(event.message));
      else if (event.type === 'done') {
        setStatus((s) => (s ? { ...s, status: event.payload.status } : s));
        if (event.payload.status === 'completed') {
          void navigate({ to: '/tutorials/$tutorialId', params: { tutorialId: instanceId }, replace: true });
        }
      }
    };
    const off = streamGeneration(instanceId, handle);
    setUnsubscribe(() => off);
    return off;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [instanceId]);

  if (error) {
    return (
      <div className="space-y-4">
        <ErrorState error={error} />
        <Button
          onClick={() => {
            setError(null);
            unsubscribe?.();
            void retry(instanceId);
          }}
        >
          Retry generation
        </Button>
      </div>
    );
  }
  if (!status) return <Loading label="Connecting to the generation stream…" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Generating tutorial</h1>
      <div className="rounded-lg border p-4">
        <div className="flex items-center justify-between">
          <span className="font-medium">{status.current_step ?? 'Preparing'}</span>
          <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs uppercase">{status.status}</span>
        </div>
        {status.step_status ? <p className="mt-1 text-sm text-neutral-500">{status.step_status}</p> : null}
        {status.error_message ? <p className="mt-2 text-sm text-red-600">{status.error_message}</p> : null}
      </div>
      <div className="flex gap-3">
        <Button variant="secondary" onClick={unsubscribe ?? undefined}>Stop watching</Button>
        <Link to="/tutorials" className="text-sm underline">Back to library</Link>
      </div>
    </div>
  );
}
