'use client'

import React from 'react'
import Link from 'next/link'
import { useAuth } from '@/app/contexts/AuthContext'
import { LogOut, User, Upload, FileText, Home } from 'lucide-react'

export default function Header() {
  const { user, logout, isLoggedIn } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">BN</span>
            </div>
            <span className="text-xl font-bold text-gray-900">Brain_Net</span>
          </Link>

          {/* Navigation */}
          {isLoggedIn && (
            <nav className="flex items-center space-x-6">
              <Link
                href="/"
                className="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              >
                <Home className="w-4 h-4" />
                <span>Home</span>
              </Link>
              <Link
                href="/docQA"
                className="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span>Upload & Process</span>
              </Link>
              <Link
                href="/files"
                className="flex items-center space-x-1 text-gray-600 hover:text-blue-600 transition-colors"
              >
                <FileText className="w-4 h-4" />
                <span>My Files</span>
              </Link>
            </nav>
          )}

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {isLoggedIn ? (
              <>
                <div className="flex items-center space-x-2">
                  <User className="w-5 h-5 text-gray-600" />
                  <span className="text-sm font-medium text-gray-700">
                    {user?.full_name || user?.username || user?.email}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 text-gray-600 hover:text-red-600 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  href="/login"
                  className="text-gray-600 hover:text-blue-600 transition-colors"
                >
                  Login
                </Link>
                <Link
                  href="/signup"
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
} 