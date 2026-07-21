'use client';

import { AxiosError } from 'axios';
import { Form } from 'antd';
import type { FormProps } from 'antd';
import {
  UserOutlined,
  MailOutlined,
  LockOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import Link from 'next/link';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import ReploInput from '@/components/ui/input/Input';
import Button from '@/components/ui/button/Button.jsx';
import { signup as signUpService } from '@/services/authService';

type SignUpRequest = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
};

type SignUpResponse = {
  user_id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
};

export default function RegisterPage() {
  const [form] = Form.useForm();
  const router = useRouter();

  const signUpMutation = useMutation<SignUpResponse, AxiosError, SignUpRequest>(
    {
      mutationFn: async (credentials: SignUpRequest) => {
        const response = await signUpService(
          credentials.first_name,
          credentials.last_name,
          credentials.email,
          credentials.password
        );
        return response.data as SignUpResponse;
      },
      onSuccess: () => {
        toast.success('Account created successfully! Welcome aboard! 🚀');
        form.resetFields();
        setTimeout(() => {
          router.push('/login');
        }, 1500);
      },
      onError: (error: AxiosError) => {
        const detail = (error.response?.data as any)?.detail;
        toast.error(detail || 'Unable to create account. Please try again.');
      },
    }
  );

  const handleSubmit: FormProps['onFinish'] = values => {
    signUpMutation.mutate({
      first_name: values.first_name,
      last_name: values.last_name,
      email: values.email,
      password: values.password,
    });
  };

  return (
    <main className="h-screen flex items-center justify-center p-4 md:p-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-50">
        <div className="absolute top-20 left-10 w-72 h-72 bg-purple-300 rounded-full opacity-40 blur-3xl animate-float mix-blend-multiply" />
        <div className="absolute top-40 right-10 w-72 h-72 bg-blue-300 rounded-full opacity-40 blur-3xl animate-float-delay-1 mix-blend-multiply" />
        <div className="absolute bottom-20 left-1/2 w-72 h-72 bg-pink-300 rounded-full opacity-40 blur-3xl animate-float-delay-2 mix-blend-multiply" />
      </div>

      <div className="relative z-10 w-full max-w-md">
        <div className="bg-white/90 backdrop-blur-sm h-[calc(100vh - 150px)] rounded-2xl shadow-xl border border-gray-200 p-8 md:p-7">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 mb-4 shadow-lg">
              <RocketOutlined className="text-2xl !text-white" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-2">
              Join Replo
            </h1>
            <p className="text-gray-600 text-sm md:text-base">
              Turn any codebase into step-by-step interactive tutorials
            </p>
          </div>

          <Form
            form={form}
            name="signup"
            onFinish={handleSubmit}
            autoComplete="off"
            layout="vertical"
            size="large"
            requiredMark={false}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <Form.Item
                name="first_name"
                rules={[
                  { required: true, message: 'Please enter your first name' },
                  {
                    min: 2,
                    message: 'First name must be at least 2 characters',
                  },
                  {
                    max: 50,
                    message: 'First name must be less than 50 characters',
                  },
                ]}
              >
                <ReploInput
                  required
                  title="First Name"
                  kind="text"
                  placeholder="John"
                  size="large"
                  className="rounded-lg"
                />
              </Form.Item>

              <Form.Item name="last_name" rules={[{ required: false }]}>
                <ReploInput
                  title="Last Name"
                  kind="text"
                  placeholder="Doe"
                  size="large"
                  className="rounded-lg"
                />
              </Form.Item>
            </div>

            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Please enter your email' },
                {
                  type: 'email',
                  message: 'Please enter a valid email address',
                },
              ]}
              className="mb-4"
            >
              <ReploInput
                required
                title="Email"
                kind="email"
                placeholder="you@example.com"
                size="large"
                className="rounded-lg"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: 'Please enter your password' },
                { min: 8, message: 'Password must be at least 8 characters' },
                {
                  max: 72,
                  message: 'Password must be less than 72 characters',
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
                className="rounded-lg"
                visibilityToggle
              />
            </Form.Item>

            <Form.Item className="mb-4">
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={signUpMutation.isPending}
                className="h-12 rounded-lg font-semibold text-base text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5 !bg-gradient-to-r !from-indigo-600 !to-purple-600 hover:!from-indigo-700 hover:!to-purple-700 border-0"
                icon={<RocketOutlined />}
              >
                {signUpMutation.isPending
                  ? 'Creating Account...'
                  : 'Create Account'}
              </Button>
            </Form.Item>
          </Form>

          <div className="text-center mt-6">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link
                href="/login"
                className="font-semibold text-indigo-600 hover:text-purple-600 transition-colors"
              >
                Sign In
              </Link>
            </p>
          </div>
        </div>

        <p className="text-center mb-6 !mt-2 text-xs text-gray-500">
          By creating an account, you agree to our Terms of Service and Privacy
          Policy
        </p>
      </div>
    </main>
  );
}
