import clsx from 'clsx'

const variants = {
  default: 'bg-vanguard-surface text-vanguard-text',
  accent: 'bg-vanguard-accent text-black',
  success: 'bg-emerald-400 text-black',
  warning: 'bg-vanguard-warning text-black',
  danger: 'bg-vanguard-danger text-white',
  muted: 'bg-[#1a2332] text-vanguard-muted',
}

const sizes = {
  sm: 'px-2 py-0.5 text-[10px]',
  md: 'px-3 py-1 text-xs',
  lg: 'px-4 py-1.5 text-sm',
}

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className,
  ...props
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5',
        'font-bold uppercase tracking-widest',
        'border-2 border-black',
        'shadow-brutal-sm',
        'whitespace-nowrap',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {dot && (
        <span
          className={clsx(
            'h-2 w-2 shrink-0 rounded-full border border-black',
            variant === 'success' && 'bg-emerald-600',
            variant === 'warning' && 'bg-orange-600',
            variant === 'danger' && 'bg-red-900',
            variant === 'accent' && 'bg-black',
            !['success', 'warning', 'danger', 'accent'].includes(variant) &&
              'bg-vanguard-accent',
          )}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  )
}