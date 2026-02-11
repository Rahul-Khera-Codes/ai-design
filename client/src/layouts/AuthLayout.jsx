import { Link, Outlet } from 'react-router-dom'

function AuthLayout() {
  return (
    <div className="min-h-screen w-full bg-gray-50 text-gray-900 relative overflow-hidden">
      {/* Subtle grid pattern */}
      <div className="pointer-events-none fixed inset-0 bg-[linear-gradient(rgba(0,0,0,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.02)_1px,transparent_1px)] bg-[size:40px_40px]" />
      
      {/* Top navigation */}
      <header className="relative z-10 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 md:px-8 py-4">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="h-9 w-1 rounded-full bg-gray-900 shadow-lg shadow-gray-900/10 group-hover:shadow-gray-900/20 transition-all" />
            <div>
              <p className="text-sm font-semibold tracking-wider text-gray-900 uppercase">
                AI IPVOYAGE
              </p>
              <p className="text-[10px] text-gray-500 mt-0.5">Secure Platform</p>
            </div>
          </Link>
        </div>
      </header>

      {/* Center layout */}
      <main className="relative z-10 flex min-h-[calc(100vh-5rem)] items-center justify-center px-4 py-12">
        {/* Auth card */}
        <section className="relative w-full max-w-md">
          <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-xl">
            <Outlet />
          </div>
        </section>
      </main>
    </div>
  )
}

export default AuthLayout
