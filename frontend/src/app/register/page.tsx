"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useEffect } from "react";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState("Analyst");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const { user, login } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) router.replace("/dashboard");
  }, [user, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/register", {
        email,
        password,
        role,
      });

      setSuccess("Account created successfully! Signing you in...");
      
      // Auto-login user after successful registration
      try {
        await login(email, password);
        router.push("/dashboard");
      } catch {
        router.push("/login?registered=true");
      }
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      const msg =
        axiosError.response?.data?.detail ||
        "Registration failed. Please check your information and try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50 px-4 py-8">
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <h1 className="text-xl font-semibold text-slate-900 tracking-tight">
            FlowGuard AI
          </h1>
          <p className="text-[13px] text-slate-500 mt-1">
            Create a new account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              Email address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 text-[13px] border border-slate-200 rounded bg-white focus:outline-none focus:border-slate-400 transition-colors"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 text-[13px] border border-slate-200 rounded bg-white focus:outline-none focus:border-slate-400 transition-colors"
            >
              <option value="Analyst">Analyst (Read-only analytics & reports)</option>
              <option value="Manager">Manager (Upload datasets & train models)</option>
              <option value="Admin">Admin (Full administrative access)</option>
            </select>
          </div>

          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 text-[13px] border border-slate-200 rounded bg-white focus:outline-none focus:border-slate-400 transition-colors"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full px-3 py-2 text-[13px] border border-slate-200 rounded bg-white focus:outline-none focus:border-slate-400 transition-colors"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-[12px] text-red-600 bg-red-50 p-2.5 rounded border border-red-100">
              {error}
            </p>
          )}

          {success && (
            <p className="text-[12px] text-emerald-700 bg-emerald-50 p-2.5 rounded border border-emerald-100">
              {success}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 text-[13px] font-medium text-white bg-slate-900 rounded hover:bg-slate-800 disabled:opacity-50 transition-colors"
          >
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>

        <div className="mt-6 text-center text-[12px] text-slate-500">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-slate-900 hover:underline"
          >
            Sign in
          </Link>
        </div>

        <p className="mt-6 text-[12px] text-slate-400 text-center">
          Procure-to-Pay process intelligence platform
        </p>
      </div>
    </div>
  );
}
