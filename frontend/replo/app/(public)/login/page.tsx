'use client';

import { useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useSearchParams } from 'next/navigation';
import { AxiosError } from 'axios';
import { Form } from 'antd';
import type { FormProps } from 'antd';
import {
  LoginOutlined,
  MailOutlined,
  LockOutlined,
  ArrowRightOutlined,
  StarFilled,
} from '@ant-design/icons';
import Link from 'next/link';
import { toast } from 'sonner';

import ReploInput from '@/components/ui/input/Input';
import Button from '@/components/ui/button/Button';
import { login as loginService } from '@/services/authService';
import { useGlobalStore } from '@/store/useGlobalStore';
import { LogIn } from 'lucide-react';

// Local types for strong typing
type Credentials = { email: string; password: string };
type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: { id?: string; email?: string; username?: string };
};

export default function LoginPage() {
  const [form] = Form.useForm();
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
      return loginService(credentials.email, credentials.password);
    },

    onSuccess: (data: LoginResponse) => {
      toast.success('Welcome back! Redirecting...');
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

  const handleSubmit: FormProps['onFinish'] = (values: Credentials) => {
    loginMutation.mutate({
      email: values.email,
      password: values.password,
    });
  };

  return (
    <main className="h-screen flex flex-col items-center justify-center p-4 md:p-6 relative overflow-hidden">
      {/* Animated gradient background with floating orbs */}
      <div className="absolute inset-0 bg-gradient-to-br from-violet-100 via-indigo-50 via-purple-50 to-cyan-50">
        <div className="absolute top-10 left-10 w-96 h-96 bg-violet-400 rounded-full opacity-30 blur-3xl animate-float mix-blend-multiply" />
        <div className="absolute top-32 right-20 w-96 h-96 bg-indigo-400 rounded-full opacity-30 blur-3xl animate-float-delay-1 mix-blend-multiply" />
        <div className="absolute bottom-10 left-1/3 w-96 h-96 bg-purple-400 rounded-full opacity-30 blur-3xl animate-float-delay-2 mix-blend-multiply" />
        <div className="absolute bottom-32 right-10 w-80 h-80 bg-cyan-400 rounded-full opacity-25 blur-3xl animate-float mix-blend-multiply" />
      </div>

      {/* Logo Header */}
      <div className="relative z-10 mb-6 md:mb-0 text-center">
        <div className="inline-flex items-center gap-2 md:gap-3 lg:gap-4 group cursor-default">
          {/* Sparkle icons - Left side with AI gradient glow */}
          <div
            className="relative"
            style={{
              background:
                'linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%)',
              borderRadius: '50%',
              padding: '4px',
            }}
          >
            <StarFilled
              className="text-2xl md:text-3xl lg:text-4xl text-white animate-pulse group-hover:animate-spin transition-all duration-500"
              style={{
                filter: 'drop-shadow(0 0 8px rgba(139, 92, 246, 0.8))',
                display: 'block',
              }}
            />
          </div>
          <div
            className="relative"
            style={{
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              borderRadius: '50%',
              padding: '3px',
            }}
          >
            <StarFilled
              className="text-xl md:text-2xl lg:text-3xl text-white animate-pulse"
              style={{
                animationDelay: '0.3s',
                filter: 'drop-shadow(0 0 6px rgba(96, 165, 250, 0.7))',
                display: 'block',
              }}
            />
          </div>
          <div
            className="relative"
            style={{
              background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
              borderRadius: '50%',
              padding: '2px',
            }}
          >
            <StarFilled
              className="text-lg md:text-xl lg:text-2xl text-white animate-pulse"
              style={{
                animationDelay: '0.6s',
                filter: 'drop-shadow(0 0 6px rgba(167, 139, 250, 0.7))',
                display: 'block',
              }}
            />
          </div>

          {/* Main Logo Text */}
          <h1 className="text-4xl !mb-4 md:text-6xl lg:text-7xl xl:text-8xl font-black bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent tracking-tight drop-shadow-sm hover:scale-105 transition-transform duration-300">
            Replo AI
          </h1>

          {/* Sparkle icons - Right side with AI gradient glow */}
          <div
            className="relative"
            style={{
              background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
              borderRadius: '50%',
              padding: '2px',
            }}
          >
            <StarFilled
              className="text-lg md:text-xl lg:text-2xl text-white animate-pulse"
              style={{
                animationDelay: '0.9s',
                filter: 'drop-shadow(0 0 6px rgba(167, 139, 250, 0.7))',
                display: 'block',
              }}
            />
          </div>
          <div
            className="relative"
            style={{
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              borderRadius: '50%',
              padding: '3px',
            }}
          >
            <StarFilled
              className="text-xl md:text-2xl lg:text-3xl text-white animate-pulse"
              style={{
                animationDelay: '1.2s',
                filter: 'drop-shadow(0 0 6px rgba(96, 165, 250, 0.7))',
                display: 'block',
              }}
            />
          </div>
          <div
            className="relative"
            style={{
              background:
                'linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%)',
              borderRadius: '50%',
              padding: '4px',
            }}
          >
            <StarFilled
              className="text-2xl md:text-3xl lg:text-4xl text-white animate-pulse group-hover:animate-spin transition-all duration-500"
              style={{
                animationDelay: '1.5s',
                filter: 'drop-shadow(0 0 8px rgba(139, 92, 246, 0.8))',
                display: 'block',
              }}
            />
          </div>
        </div>
        <p className="mt-3 md:mt-4 text-xs md:text-sm text-gray-600 font-semibold tracking-[0.2em] uppercase">
          Intelligent Learning Platform
        </p>
      </div>

      <div className="relative z-10 w-full max-w-md mx-auto">
        <div className="bg-white/95 backdrop-blur-md rounded-3xl shadow-2xl border border-white/50 p-8 md:p-10">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 mb-5 shadow-xl transform transition-transform hover:scale-110">
              <LoginOutlined className="text-3xl !text-white" />
            </div>
            <h1 className="text-2xl !mb-2 md:text-5xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
              Welcome Back
            </h1>
            <p className="text-gray-600 text-sm md:text-base">
              Continue your learning journey with Replo
            </p>
          </div>

          <Form
            form={form}
            name="login"
            onFinish={handleSubmit}
            autoComplete="off"
            layout="vertical"
            size="large"
            requiredMark={false}
          >
            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Please enter your email' },
                {
                  type: 'email',
                  message: 'Please enter a valid email address',
                },
              ]}
              className="mb-5"
            >
              <ReploInput
                required
                title="Email"
                kind="email"
                placeholder="you@example.com"
                size="large"
                className="rounded-xl border-gray-200 hover:border-indigo-400 focus-within:!border-indigo-500 transition-colors"
                prefix={<MailOutlined className="text-indigo-500 text-lg" />}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: 'Please enter your password' },
                {
                  min: 8,
                  message: 'Password must be at least 8 characters',
                },
              ]}
              className="mb-6"
            >
              <ReploInput
                required
                title="Password"
                kind="password"
                placeholder="••••••••"
                size="large"
                className="rounded-xl border-gray-200 hover:border-indigo-400 focus-within:!border-indigo-500 transition-colors"
                prefix={<LockOutlined className="text-indigo-500 text-lg" />}
                visibilityToggle
              />
            </Form.Item>

            <Form.Item className="mb-4">
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={loginMutation.isPending}
                className="h-14 rounded-xl font-semibold text-lg text-white shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 !bg-gradient-to-r !from-indigo-600 !via-purple-600 !to-pink-600 hover:!from-indigo-700 hover:!via-purple-700 hover:!to-pink-700 border-0 bg-[length:200%_auto] hover:bg-[position:100%_center]"
                icon={<LogIn className="!text-lg" />}
              >
                {loginMutation.isPending ? 'Signing in...' : 'Sign In'}
              </Button>
            </Form.Item>
          </Form>

          <div className="text-center mt-6">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link
                href="/signup"
                className="font-semibold text-indigo-600 hover:text-purple-600 transition-colors hover:underline"
              >
                Create Account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
