"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import SearchBar from "./SearchBar";

export default function Navbar() {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-dark-900/95 backdrop-blur-sm border-b border-dark-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link
            href="/"
            className="text-xl font-bold text-white hover:text-accent-blue transition-colors shrink-0"
          >
            AI 인사이트
          </Link>

          <div className="hidden md:block flex-1 max-w-md mx-8">
            <SearchBar />
          </div>

          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <>
                <span className="text-sm text-gray-400">
                  {user.username}
                </span>
                <Link
                  href="/mypage"
                  className="text-sm text-gray-300 hover:text-white transition-colors"
                >
                  마이페이지
                </Link>
                {user.role === "ADMIN" && (
                  <Link
                    href="/admin"
                    className="text-sm text-accent-blue hover:text-accent-hover transition-colors"
                  >
                    관리자
                  </Link>
                )}
                <button
                  onClick={logout}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  로그아웃
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="btn-secondary text-sm">
                  로그인
                </Link>
                <Link href="/register" className="btn-primary text-sm">
                  회원가입
                </Link>
              </>
            )}
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-dark-800 transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              {mobileMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden border-t border-dark-700 bg-dark-900">
          <div className="px-4 py-4 space-y-3">
            <SearchBar />
            {user ? (
              <>
                <div className="text-sm text-gray-400 pt-2">
                  {user.username}
                </div>
                <Link
                  href="/mypage"
                  className="block text-sm text-gray-300 hover:text-white py-1"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  마이페이지
                </Link>
                {user.role === "ADMIN" && (
                  <Link
                    href="/admin"
                    className="block text-sm text-accent-blue hover:text-accent-hover py-1"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    관리자
                  </Link>
                )}
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="block text-sm text-gray-400 hover:text-white py-1"
                >
                  로그아웃
                </button>
              </>
            ) : (
              <div className="flex gap-3 pt-2">
                <Link
                  href="/login"
                  className="btn-secondary text-sm flex-1 text-center"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  로그인
                </Link>
                <Link
                  href="/register"
                  className="btn-primary text-sm flex-1 text-center"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  회원가입
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
