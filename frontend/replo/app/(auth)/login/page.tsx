// ./frontend/src/app/(auth)/login/page.tsx
"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";
import { toast } from "sonner";

import { login as loginService } from "@/services/authService"; // Import your service
import { useGlobalStore } from "@/store/useGlobalStore"; // Import your store

// Local types for strong typing
type Credentials = { email: string; password: string };
type LoginResponse = {
  access_token: string;
  token_type: string;
  user: { id?: string; email?: string; username?: string };
};

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  
  const router = useRouter();
  
  // Get the login action from your Zustand store
  const loginAction = useGlobalStore((state: any) => state.login);

  const loginMutation = useMutation<LoginResponse, AxiosError, Credentials>({
    mutationFn: async (credentials: Credentials) => {
      // apiClient returns response.data already
      return loginService(credentials.email, credentials.password);
    },
    
    onSuccess: (data: LoginResponse) => {
        toast.success("Login successful! Redirecting...");
      // 1. Save user and token
      loginAction(data.user, data.access_token);
      
      // 2. Redirect to the dashboard
      router.push("/dashboard");
    },
    
    onError: (error: AxiosError) => {
      console.error("Login failed:", error);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const detail = (error.response?.data as any)?.detail;
      toast.error(detail || "An unknown error occurred");
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    loginMutation.mutate({ email, password });
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <form 
        onSubmit={handleSubmit}
        className="p-8 bg-white shadow-md rounded"
      >
        <h1 className="text-2xl font-bold mb-4 text-black">Login</h1>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full p-2 mb-4 border rounded text-black"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full p-2 mb-4 border rounded text-black"
          required
        />
        <button
          type="submit"
          disabled={loginMutation.isPending}
          className="w-full p-2 bg-blue-600 text-white rounded"
        >
          {loginMutation.isPending ? "Logging in..." : "Login"}
        </button>
      </form>
    </div>
  );
}