import { FormEvent, useState } from 'react';
import { Link, useNavigate } from '@tanstack/react-router';
import { Button } from '@replo/ui';
import { login, oauthAuthorizeUrl, signup } from '@/services/auth';
import { adoptSession } from '@/lib/api';
import { ErrorState } from '@/components/states';
import type { OAuthProvider } from '@replo/api-client';

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      adoptSession(await login(email, password));
      void navigate({ to: '/tutorials' });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const oauth = async (provider: OAuthProvider) => {
    try {
      window.location.href = await oauthAuthorizeUrl(provider);
    } catch (err) {
      setError(err);
    }
  };

  return (
    <div className="mx-auto max-w-sm space-y-6 py-10">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      {error ? <ErrorState error={error} /> : null}
      <form className="space-y-3" onSubmit={submit}>
        <input className="w-full rounded-md border px-3 py-2" type="email" required placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input className="w-full rounded-md border px-3 py-2" type="password" required placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <Button className="w-full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</Button>
      </form>
      <div className="grid grid-cols-2 gap-3">
        <Button variant="secondary" onClick={() => void oauth('github')}>Continue with GitHub</Button>
        <Button variant="secondary" onClick={() => void oauth('google')}>Continue with Google</Button>
      </div>
      <p className="text-sm text-neutral-500">
        No account? <Link to="/signup" className="font-medium underline">Sign up</Link>
      </p>
    </div>
  );
}

export function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '' });
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signup(form);
      adoptSession(await login(form.email, form.password));
      void navigate({ to: '/tutorials' });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const field = (key: keyof typeof form, label: string, type = 'text') => (
    <input
      className="w-full rounded-md border px-3 py-2"
      type={type}
      required
      placeholder={label}
      value={form[key]}
      onChange={(e) => setForm({ ...form, [key]: e.target.value })}
    />
  );

  return (
    <div className="mx-auto max-w-sm space-y-6 py-10">
      <h1 className="text-2xl font-semibold">Create account</h1>
      {error ? <ErrorState error={error} /> : null}
      <form className="space-y-3" onSubmit={submit}>
        {field('first_name', 'First name')}
        {field('last_name', 'Last name')}
        {field('email', 'Email', 'email')}
        {field('password', 'Password', 'password')}
        <Button className="w-full" disabled={busy}>{busy ? 'Creating…' : 'Sign up'}</Button>
      </form>
    </div>
  );
}
