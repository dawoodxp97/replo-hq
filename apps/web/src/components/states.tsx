import { Button } from '@replo/ui';

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return <div role="status" className="animate-pulse text-sm text-neutral-500">{label}</div>;
}

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-neutral-300 p-10 text-center">
      <p className="font-medium">{title}</p>
      {hint ? <p className="mt-1 text-sm text-neutral-500">{hint}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : 'Something went wrong';
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <p>{message}</p>
      {onRetry ? <Button variant="secondary" size="sm" className="mt-3" onClick={onRetry}>Try again</Button> : null}
    </div>
  );
}
