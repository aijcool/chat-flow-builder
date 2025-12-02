'use client'

import { SignIn } from '@clerk/nextjs'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* 包豪斯几何背景 */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 left-20 w-64 h-64 bg-yellow-400 rounded-full opacity-20 blur-3xl" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500 rounded-full opacity-20 blur-3xl" />
        <div className="absolute top-1/2 left-1/3 w-48 h-48 bg-red-500 opacity-10 rotate-45" />
      </div>

      <div className="relative z-10">
        <SignIn
          appearance={{
            elements: {
              rootBox: 'mx-auto',
              card: 'bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl',
              headerTitle: 'text-white',
              headerSubtitle: 'text-white/70',
              socialButtonsBlockButton: 'bg-white/10 border-white/20 text-white hover:bg-white/20',
              formFieldLabel: 'text-white/80',
              formFieldInput: 'bg-white/10 border-white/20 text-white placeholder:text-white/40',
              footerActionLink: 'text-yellow-400 hover:text-yellow-300',
              formButtonPrimary: 'bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600',
            }
          }}
        />
      </div>
    </div>
  )
}
