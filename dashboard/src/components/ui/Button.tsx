import { cn } from '@/lib/utils'
import { ButtonHTMLAttributes, forwardRef } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
          // Variant styles
          variant === 'primary' &&
            'bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500',
          variant === 'secondary' &&
            'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 focus:ring-slate-500',
          variant === 'ghost' && 'text-slate-600 hover:bg-slate-100 focus:ring-slate-500',
          variant === 'danger' &&
            'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500',
          // Size styles
          size === 'sm' && 'px-3 py-1.5 text-sm',
          size === 'md' && 'px-4 py-2 text-sm',
          size === 'lg' && 'px-6 py-3 text-base',
          // Disabled
          disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
