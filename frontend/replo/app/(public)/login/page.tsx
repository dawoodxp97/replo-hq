// ./frontend/src/app/(auth)/login/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useSearchParams } from 'next/navigation';
import { AxiosError } from 'axios';
import { toast } from 'sonner';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';

import ReploInput from '@/components/ui/input/Input';

import { login as loginService } from '@/services/authService'; // Import your service
import { useGlobalStore } from '@/store/useGlobalStore'; // Import your store
import Button from '@/components/ui/button/Button';

// Local types for strong typing
type Credentials = { email: string; password: string };
type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: { id?: string; email?: string; username?: string };
};

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const router = useRouter();
  const searchParams = useSearchParams();

  // Store state/actions
  const loginAction = useGlobalStore((state: any) => state.login);
  const isAuthenticated = useGlobalStore((state: any) => state.isAuthenticated);

  // If already authenticated, avoid showing login and go to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isAuthenticated, router]);

  // Show error messages passed via query string (e.g., expired session)
  useEffect(() => {
    const err = searchParams.get('error');
    if (err === 'expired') {
      toast.error('Your session has expired. Please log in again.');
    } else if (err === 'unauthenticated') {
      toast.error('Please log in to continue.');
    }
  }, [searchParams]);

  const loginMutation = useMutation<LoginResponse, AxiosError, Credentials>({
    mutationFn: async (credentials: Credentials) => {
      // apiClient returns response.data already
      return loginService(credentials.email, credentials.password);
    },

    onSuccess: (data: LoginResponse) => {
      toast.success('Login successful! Redirecting...');
      // 1. Save user and both tokens
      loginAction(data.user, data.access_token, data.refresh_token);

      // 2. Redirect to the dashboard
      router.push('/dashboard');
    },

    onError: (error: AxiosError) => {
      console.error('Login failed:', error);
      const status = error.response?.status;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const detail = (error.response?.data as any)?.detail;
      if (error.code === 'ERR_NETWORK') {
        toast.error('Network error. Please check your connection.');
      } else if (status === 401 || status === 400) {
        toast.error(detail || 'Invalid email or password.');
      } else {
        toast.error(detail || 'An unknown error occurred');
      }
    },
  });

  const handleSubmit = (e: any) => {
    e?.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields.');
      return;
    }
    loginMutation.mutate({ email, password });
  };

  return (
    <div className="w-screen - bg-[var(--foreground)] flex items-center justify-center min-h-screen">
      <div className="w-1/2 bg-white flex items-center justify-center min-h-[calc(100vh-25px)] mt-3 ml-3 mb-3 rounded-l-lg shadow-xl/30">
        <form
          onSubmit={handleSubmit}
          className="w-full p-8 shadow-md rounded min-h-[calc(100vh-25px)] flex flex-col justify-center "
        >
          <div>
            <p className="text-2xl font-bold mb-4 text-black text-center mt-[10px]">
              Login
            </p>
            <div className="mt-4 mb-4">
              <ReploInput
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="Email"
                className="w-full p-2 border rounded text-black"
                required
              />
            </div>
            <div className="mt-4 mb-4">
              <ReploInput
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Password"
                className="w-full p-2 border rounded text-black"
                required
              />
            </div>
            <div className="mt-4 mb-4">
              <Button
                onClick={e => handleSubmit(e)}
                type="primary"
                disabled={loginMutation.isPending}
                className="w-full p-2 bg-blue-600 text-white rounded"
              >
                {loginMutation.isPending ? 'Logging in...' : 'Login'}
              </Button>
            </div>
          </div>
        </form>
      </div>
      <div className="w-1/2 flex items-center justify-center min-h-[calc(100vh-25px)] mt-3 mr-3 mb-3 bg-gradient-to-r from-[#6a11cb] to-[#2575fc] rounded-r-lg shadow-xl/30">
        <DotLottieReact
          src="https://lottie.host/84513c27-0a47-404b-b817-919ca2982e2b/OS1rPcz3Y1.lottie"
          loop
          autoplay
        />
      </div>
    </div>
  );
}
