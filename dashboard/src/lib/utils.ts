import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatVenueType(type: string): string {
  const map: Record<string, string> = {
    college_d1: 'D1 College',
    college_d2: 'D2 College',
    college_d3: 'D3 College',
    college_naia: 'NAIA College',
    high_school_6a: 'High School 6A',
    high_school_5a: 'High School 5A',
    high_school_4a: 'High School 4A',
    high_school_3a: 'High School 3A',
    high_school_other: 'High School',
  }
  return map[type] || type
}

export function formatStatus(status: string): string {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export const TIER_COLORS: Record<string, string> = {
  A1: 'bg-green-100 text-green-800 border-green-200',
  A2: 'bg-blue-100 text-blue-800 border-blue-200',
  B: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  C: 'bg-orange-100 text-orange-800 border-orange-200',
  D: 'bg-red-100 text-red-800 border-red-200',
}

export const STATUS_COLORS: Record<string, string> = {
  identified: 'bg-slate-100 text-slate-700',
  needs_scoring: 'bg-purple-100 text-purple-700',
  scored: 'bg-blue-100 text-blue-700',
  needs_research: 'bg-indigo-100 text-indigo-700',
  research_complete: 'bg-cyan-100 text-cyan-700',
  ready_for_outreach: 'bg-teal-100 text-teal-700',
  outreach_active: 'bg-green-100 text-green-700',
  engaged: 'bg-emerald-100 text-emerald-700',
  nurture: 'bg-yellow-100 text-yellow-700',
  deprioritized: 'bg-red-100 text-red-700',
}
