"use client";

import { useState } from "react";
import { AxiosError } from "axios";

import Link from "next/link";
import Button from "@/components/Button";
// import { useGlobalStore } from "@/store/useGlobalStore"; // Removed: no signUp action in store
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { signup as signUpService } from "@/services/authService";

type SignUpRequest = {
  name: string;
  email: string;
  password: string;
};
// Backend returns UserPublic (id, email) on signup
type SignUpResponse = {
  id: number;
  email: string;
};

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  const router = useRouter();

  const signUpMutation = useMutation<SignUpResponse, AxiosError, SignUpRequest>({
    mutationFn: async (credentials: SignUpRequest) => {
      // Backend expects only email and password
      return signUpService(credentials.email, credentials.password) as unknown as SignUpResponse;
    },
    onSuccess: () => {
      toast.success("Account created! Please log in.");
      router.push("/login");
    },
    onError: (error: AxiosError) => {
      const detail = (error.response?.data as any)?.detail;
      toast.error(detail || "Unable to create account");
    },
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    signUpMutation.mutate({ name, email, password });
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm border rounded-lg p-6 bg-white">
        <h1 className="text-2xl font-bold mb-4">Register</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm mb-1" htmlFor="name">Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="Jane Doe"
              required
            />
          </div>
          <div>
            <label className="block text-sm mb-1" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="you@example.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm mb-1" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="••••••••"
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={signUpMutation.isPending}>Create Account</Button>
        </form>
        <p className="text-sm mt-4">
          Already have an account? <Link className="text-blue-600" href="/login">Login</Link>
        </p>
      </div>
    </main>
  );
}