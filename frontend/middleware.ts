import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

// 定义公开路由（不需要登录）
const isPublicRoute = createRouteMatcher([
  '/',
  '/login(.*)',
  '/signup(.*)',
  '/api/backend(.*)',  // 后端代理路由
])

export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect()
  }
})

export const config = {
  matcher: [
    // Skip Next.js internals and all static files
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
}
