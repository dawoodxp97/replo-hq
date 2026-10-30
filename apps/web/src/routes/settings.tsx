import { useCallback, useEffect, useState } from 'react';
import { Button } from '@replo/ui';
import { all as allSettings, listCredentials, addCredential, deleteCredential, revokeSessions } from '@/services/settings';
import type { CredentialResponse, UserSettingsResponse } from '@replo/api-client';
import { ErrorState, Loading } from '@/components/states';

const PROVIDERS = ['openrouter', 'anthropic', 'openai'] as const;

export function SettingsPage() {
  const [settings, setSettings] = useState<UserSettingsResponse | null>(null);
  const [creds, setCreds] = useState<CredentialResponse[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [label, setLabel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [provider, setProvider] = useState<(typeof PROVIDERS)[number]>('openrouter');

  const load = useCallback(() => {
    setError(null);
    void Promise.all([allSettings(), listCredentials()])
      .then(([s, c]) => {
        setSettings(s);
        setCreds(c);
      })
      .catch(setError);
  }, []);

  useEffect(load, [load]);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!settings) return <Loading />;

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="text-2xl font-semibold">Profile</h1>
        <div className="rounded-lg border p-4 text-sm">
          <p><span className="text-neutral-500">Email:</span> {settings.profile.email ?? ''}</p>
          <p><span className="text-neutral-500">Name:</span> {settings.profile.first_name ?? ''} {settings.profile.last_name ?? ''}</p>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">API keys (BYOK)</h2>
        <div className="space-y-2">
          {creds.length === 0 ? (
            <p className="text-sm text-neutral-500">No keys yet. Add a provider key to generate tutorials with your own account.</p>
          ) : (
            creds.map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                <div>
                  <span className="font-medium">{c.label}</span>
                  <span className="ml-2 text-neutral-500">{c.provider} ····{c.last_four}</span>
                </div>
                <Button variant="secondary" size="sm" onClick={() => void deleteCredential(c.id).then(load)}>Remove</Button>
              </div>
            ))
          )}
        </div>
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void addCredential({ label, provider, api_key: apiKey }).then(() => { setLabel(''); setApiKey(''); load(); });
          }}
        >
          <select className="rounded-md border px-2 py-2 text-sm" value={provider} onChange={(e) => setProvider(e.target.value as (typeof PROVIDERS)[number])}>
            {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <input required placeholder="Label" className="rounded-md border px-3 py-2 text-sm" value={label} onChange={(e) => setLabel(e.target.value)} />
          <input required type="password" placeholder="API key" className="w-64 rounded-md border px-3 py-2 text-sm" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          <Button type="submit" size="sm">Add key</Button>
        </form>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Security</h2>
        <Button
          variant="secondary"
          onClick={() => void revokeSessions().then(() => window.location.assign('/login'))}
        >
          Sign out everywhere
        </Button>
      </section>
    </div>
  );
}
