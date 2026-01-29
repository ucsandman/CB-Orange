'use client'

import { Bell, User } from 'lucide-react'

export function Header() {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
      <div className="text-sm text-slate-500">
        {/* Breadcrumb or page title can go here */}
      </div>

      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 relative">
          <Bell className="w-5 h-5" />
          {/* Notification badge */}
          {/* <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" /> */}
        </button>

        {/* User menu */}
        <button className="flex items-center gap-2 p-2 text-slate-600 hover:bg-slate-100 rounded-lg">
          <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-slate-500" />
          </div>
          <span className="text-sm font-medium">User</span>
        </button>
      </div>
    </header>
  )
}
