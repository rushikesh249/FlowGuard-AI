"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function ResetPasswordPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }

    if (newPassword.length < 6) {
      setError("New password must be at least 6 characters long.");
      return;
    }

    setLoading(true);
    try {
      // If user is not logged in, authenticate first to get the token
      if (!user) {
        if (!email) {
          setError("Email is required.");
          setLoading(false);
          return;
        }
        await login(email, currentPassword);
      }

      // Call the backend reset-password endpoint with the active Bearer token
      await api.post("/auth/reset-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });

      setSuccess("Password updated successfully! Redirecting...");
      setTimeout(() => {
        router.push("/dashboard");
      }, 1500);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      const msg =
        axiosError.response?.data?.detail ||
        "Failed to update password. Please verify your current password.";
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
            Reset your account password
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!user && (
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
          )}

          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full px-3 py-2 text-[13px] border border-slate-200 rounded bg-white focus:outline-none focus:border-slate-400 transition-colors"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              className="w-full px-3 py-2 text-[13px] border border-slate-200 rounded bg-white focus:outline-none focus:border-slate-400 transition-colors"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              Confirm New Password
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
            {loading ? "Updating password..." : "Reset Password"}
          </button>
        </form>

        <div className="mt-6 flex items-center justify-between text-[12px] text-slate-500">
          <Link
            href="/login"
            className="font-medium text-slate-900 hover:underline"
          >
            Back to Sign in
          </Link>
          <Link
            href="/register"
            className="text-slate-600 hover:underline"
          >
            Create account
          </Link>
        </div>

        <p className="mt-6 text-[12px] text-slate-400 text-center">
          Procure-to-Pay process intelligence platform
        </p>
      </div>
    </div>
  );
}
