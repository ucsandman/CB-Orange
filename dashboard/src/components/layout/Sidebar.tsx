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
  Zap,
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

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-navy-900 text-white flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-navy-800">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold">Sportsbeams</span>
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
        <p className="text-xs text-slate-500">Sportsbeams Pipeline v1.0</p>
      </div>
    </div>
  )
}
