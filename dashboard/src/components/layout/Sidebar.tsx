'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Users,
  Bot,
  Mail,
  BarChart3,
  Settings,
  Upload,
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Prospects', href: '/prospects', icon: Users },
  { name: 'Import', href: '/import', icon: Upload },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Outreach', href: '/outreach', icon: Mail },
  { name: 'Reports', href: '/reports', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

// CB Orange logo icon (stylized design)
function CBOrangeLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect width="40" height="40" rx="8" fill="#F4802A" />
      <path
        d="M20 8C13.4 8 8 13.4 8 20s5.4 12 12 12c3.2 0 6.1-1.2 8.3-3.2"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M20 32c6.6 0 12-5.4 12-12S26.6 8 20 8c-3.2 0-6.1 1.2-8.3 3.2"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  )
}

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-navy-900 text-white flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-navy-800">
        <Link href="/" className="flex items-center gap-3">
          <CBOrangeLogo className="w-10 h-10" />
          <div className="flex flex-col">
            <span className="text-lg font-bold text-white">CB Orange</span>
            <span className="text-xs text-slate-400">Athletic Solutions</span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href))

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-500 text-white'
                  : 'text-slate-300 hover:bg-navy-800 hover:text-white'
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-navy-800">
        <p className="text-xs text-slate-500">CB Orange Pipeline v1.0</p>
      </div>
    </div>
  )
}
