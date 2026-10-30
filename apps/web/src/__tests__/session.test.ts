import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const storage = new Map<string, string>();
vi.stubGlobal('localStorage', {
  getItem: (k: string) => storage.get(k) ?? null,
  setItem: (k: string, v: string) => void storage.set(k, v),
  removeItem: (k: string) => void storage.delete(k),
});
vi.stubGlobal('location', { pathname: '/' });

describe('session module', () => {
  beforeEach(() => storage.clear());

  it('loads a persisted session', async () => {
    storage.set('replo.session', JSON.stringify({ access_token: 'a', refresh_token: 'r', user: { user_id: 'u1', email: 'e' } }));
    const { loadSession } = await import('@/lib/api');
    expect(loadSession()?.user.user_id).toBe('u1');
  });

  it('returns null for corrupt storage', async () => {
    storage.set('replo.session', '{not json');
    const { loadSession } = await import('@/lib/api');
    expect(loadSession()).toBeNull();
  });

  it('notifies subscribers on adopt and drop', async () => {
    const { adoptSession, dropSession, subscribeSession } = await import('@/lib/api');
    let calls = 0;
    const off = subscribeSession(() => { calls += 1; });
    adoptSession({ access_token: 'a', refresh_token: 'r', user: { user_id: 'u', email: 'e' } });
    dropSession();
    off();
    expect(calls).toBe(2);
  });
});

describe('refresh single-flight', () => {
  afterEach(() => vi.restoreAllMocks());

  it('replays the original request after refreshing', async () => {
    let refreshed = 0;
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const req = input instanceof Request ? input : new Request(input, init);
      const url = req.url;
      const auth = req.headers.get('Authorization');
      if (url.includes('/api/user/refresh')) {
        refreshed += 1;
        return new Response(JSON.stringify({ access_token: 'a2', refresh_token: 'r2', user: { user_id: 'u', email: 'e' } }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (auth === 'Bearer a2') return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      return new Response(JSON.stringify({ detail: 'expired' }), { status: 401, headers: { 'Content-Type': 'application/json' } });
    }));

    const mod = await import('@/lib/api');
    mod.adoptSession({ access_token: 'a1', refresh_token: 'r1', user: { user_id: 'u', email: 'e' } });

    const call = await import('@replo/api-client').then((c) => c.listTutorialsApiTutorialGet({}));
    console.log('CALL', JSON.stringify(call));
    expect(refreshed).toBe(1);
    expect(call.data).toEqual({ ok: true });
  });
});
