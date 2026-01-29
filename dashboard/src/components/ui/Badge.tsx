import { cn, TIER_COLORS, STATUS_COLORS, formatStatus } from '@/lib/utils'

interface TierBadgeProps {
  tier: string | null | undefined
}

export function TierBadge({ tier }: TierBadgeProps) {
  if (!tier) return null

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border',
        TIER_COLORS[tier] || 'bg-slate-100 text-slate-700'
      )}
    >
      {tier}
    </span>
  )
}

interface StatusBadgeProps {
  status: string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        STATUS_COLORS[status] || 'bg-slate-100 text-slate-700'
      )}
    >
      {formatStatus(status)}
    </span>
  )
}
