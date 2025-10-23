// ./frontend/src/app/(auth)/login/page.tsx
"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";

import { login as loginService } from "@/services/authService"; // Import your service
import { useGlobalStore } from "@/store/useGlobalStore"; // Import your store

// Local types for strong typing
type Credentials = { email: string; password: string };
type LoginResponse = {
  token: { access_token: string };
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
      const response = await loginService(credentials.email, credentials.password);
      return response.data; // Extract the actual data from AxiosResponse
    },
    
    onSuccess: (data: LoginResponse) => {
      // 'data' is the response: { token: {...}, user: {...} }
      // 1. Call your Zustand action to save state
      loginAction(data.user, data.token.access_token);
      
      // 2. Redirect to the dashboard
      router.push("/dashboard");
    },
    
    onError: (error: AxiosError) => {
      // React Query's 'error' object
      console.error("Login failed:", error);
      // You can show an error message to the user here
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const detail = (error.response?.data as any)?.detail;
      alert(detail || "Login failed");
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