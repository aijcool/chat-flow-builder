'use client'

import Link from 'next/link'
import { useAuth } from '@clerk/nextjs'
import { ArrowRight, Sparkles, Zap, Layers } from 'lucide-react'

export default function HomePage() {
  const { isSignedIn } = useAuth()

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      {/* 包豪斯几何背景 */}
      <div className="fixed inset-0 pointer-events-none">
        {/* 大圆 */}
        <div className="absolute -top-32 -left-32 w-[500px] h-[500px] bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full opacity-20 blur-3xl animate-pulse" />
        <div className="absolute -bottom-48 -right-48 w-[600px] h-[600px] bg-gradient-to-br from-blue-500 to-cyan-400 rounded-full opacity-15 blur-3xl" />

        {/* 几何形状 */}
        <div className="absolute top-1/4 right-1/4 w-32 h-32 border-4 border-red-500/30 rotate-45 animate-spin-slow" />
        <div className="absolute bottom-1/3 left-1/4 w-24 h-24 bg-yellow-500/20 rotate-12" />
        <div className="absolute top-1/2 right-1/3 w-16 h-16 bg-blue-500/30 rounded-full" />
        <div className="absolute bottom-1/4 right-1/5 w-20 h-20 border-2 border-white/10 rounded-full" />

        {/* 线条装饰 */}
        <div className="absolute top-0 left-1/3 w-px h-full bg-gradient-to-b from-transparent via-white/5 to-transparent" />
        <div className="absolute top-0 right-1/4 w-px h-full bg-gradient-to-b from-transparent via-yellow-500/10 to-transparent" />
      </div>

      {/* 导航栏 */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
            <Layers className="w-6 h-6 text-slate-950" />
          </div>
          <span className="text-xl font-bold tracking-tight">Chatflow Tailor</span>
        </div>

        <div className="flex items-center gap-4">
          {isSignedIn ? (
            <Link
              href="/studio"
              className="px-6 py-2.5 bg-gradient-to-r from-yellow-400 to-orange-500 text-slate-950 font-semibold rounded-full hover:shadow-lg hover:shadow-yellow-500/25 transition-all duration-300"
            >
              进入工作台
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="px-5 py-2 text-white/80 hover:text-white transition-colors"
              >
                登录
              </Link>
              <Link
                href="/signup"
                className="px-6 py-2.5 bg-gradient-to-r from-yellow-400 to-orange-500 text-slate-950 font-semibold rounded-full hover:shadow-lg hover:shadow-yellow-500/25 transition-all duration-300"
              >
                免费开始
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 flex flex-col items-center justify-center min-h-[calc(100vh-100px)] px-8">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-full mb-8">
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-white/70">Powered by Claude AI</span>
          </div>

          {/* 主标题 */}
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
            <span className="bg-gradient-to-r from-white via-white to-white/60 bg-clip-text text-transparent">
              用自然语言
            </span>
            <br />
            <span className="bg-gradient-to-r from-yellow-400 via-orange-400 to-red-500 bg-clip-text text-transparent">
              创造对话流程
            </span>
          </h1>

          {/* 副标题 */}
          <p className="text-xl md:text-2xl text-white/60 max-w-2xl mx-auto mb-12 leading-relaxed">
            描述你想要的对话流程，AI 自动生成专业的
            <span className="text-white/90"> Agent Studio Chatflow</span>
          </p>

          {/* CTA 按钮 */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href={isSignedIn ? '/studio' : '/signup'}
              className="group flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-yellow-400 to-orange-500 text-slate-950 font-bold text-lg rounded-full hover:shadow-xl hover:shadow-yellow-500/30 transition-all duration-300 hover:scale-105"
            >
              开始创建
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="#features"
              className="px-8 py-4 border border-white/20 text-white/80 font-medium rounded-full hover:bg-white/5 hover:border-white/30 transition-all duration-300"
            >
              了解更多
            </a>
          </div>
        </div>

        {/* 装饰性流程图预览 */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 opacity-30">
          <div className="w-24 h-12 bg-blue-500/30 rounded-lg backdrop-blur-sm" />
          <div className="w-8 h-0.5 bg-white/30" />
          <div className="w-24 h-12 bg-green-500/30 rounded-lg backdrop-blur-sm" />
          <div className="w-8 h-0.5 bg-white/30" />
          <div className="w-24 h-12 bg-yellow-500/30 rounded-lg backdrop-blur-sm" />
        </div>
      </main>

      {/* Features Section */}
      <section id="features" className="relative z-10 py-32 px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">为什么选择 Chatflow Tailor</h2>
            <p className="text-white/60 text-lg">AI 驱动的工作流生成，让复杂变简单</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group p-8 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl hover:bg-white/10 hover:border-white/20 transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Sparkles className="w-7 h-7 text-slate-950" />
              </div>
              <h3 className="text-xl font-semibold mb-3">自然语言输入</h3>
              <p className="text-white/60 leading-relaxed">
                用中文描述你的需求，AI 自动理解并生成完整的对话流程，无需编程知识
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group p-8 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl hover:bg-white/10 hover:border-white/20 transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-cyan-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap className="w-7 h-7 text-slate-950" />
              </div>
              <h3 className="text-xl font-semibold mb-3">实时预览编辑</h3>
              <p className="text-white/60 leading-relaxed">
                生成的流程可视化展示，支持拖拽编辑、节点调整，所见即所得
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group p-8 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl hover:bg-white/10 hover:border-white/20 transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-red-400 to-pink-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Layers className="w-7 h-7 text-slate-950" />
              </div>
              <h3 className="text-xl font-semibold mb-3">一键导出</h3>
              <p className="text-white/60 leading-relaxed">
                生成标准 JSON 格式，直接导入 Agent Studio 使用，无缝衔接工作流
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-8 px-8 border-t border-white/10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2 text-white/40">
            <Layers className="w-5 h-5" />
            <span>Chatflow Tailor</span>
          </div>
          <p className="text-white/40 text-sm">
            Built with Claude AI & Next.js
          </p>
        </div>
      </footer>

      {/* 自定义动画 */}
      <style jsx>{`
        @keyframes spin-slow {
          from {
            transform: rotate(45deg);
          }
          to {
            transform: rotate(405deg);
          }
        }
        .animate-spin-slow {
          animation: spin-slow 20s linear infinite;
        }
      `}</style>
    </div>
  )
}
