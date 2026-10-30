import { FormEvent, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Button } from '@replo/ui';
import { generate } from '@/services/tutorials';
import { ErrorState } from '@/components/states';
import type { TutorialLevel } from '@replo/api-client';

export function GeneratePage() {
  const navigate = useNavigate();
  const [repoUrl, setRepoUrl] = useState('');
  const [difficulty, setDifficulty] = useState<TutorialLevel>('beginner');
  const [focus, setFocus] = useState('');
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { instance_id } = await generate({
        repoUrl,
        difficulty,
        focus: focus ? focus.split(',').map((s) => s.trim()).filter(Boolean) : null,
      });
      void navigate({ to: '/generation/$instanceId', params: { instanceId: instance_id } });
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Generate a tutorial</h1>
      {error ? <ErrorState error={error} /> : null}
      <form className="space-y-4" onSubmit={submit}>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="repo">GitHub repository URL</label>
          <input id="repo" required placeholder="https://github.com/org/repo" className="w-full rounded-md border px-3 py-2" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="level">Level</label>
          <select id="level" className="w-full rounded-md border px-3 py-2" value={difficulty} onChange={(e) => setDifficulty(e.target.value as TutorialLevel)}>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="focus">Focus topics (optional, comma-separated)</label>
          <input id="focus" placeholder="auth, caching" className="w-full rounded-md border px-3 py-2" value={focus} onChange={(e) => setFocus(e.target.value)} />
        </div>
        <Button type="submit" disabled={busy}>{busy ? 'Starting…' : 'Generate'}</Button>
      </form>
    </div>
  );
}
