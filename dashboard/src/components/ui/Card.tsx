import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className, ...props }: CardProps) {
  return (
    <div
      className={cn('bg-white rounded-lg border border-slate-200 shadow-sm', className)}
      {...props}
    >
      {children}
    </div>
  )
}
