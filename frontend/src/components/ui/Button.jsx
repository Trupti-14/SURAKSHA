import clsx from 'clsx'

const variants = {
  primary:
    'bg-vanguard-accent text-black hover:bg-vanguard-accent-dim active:translate-x-[2px] active:translate-y-[2px] active:shadow-none',
  secondary:
    'bg-vanguard-surface text-vanguard-text hover:bg-[#1a2332] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none',
  danger:
    'bg-vanguard-danger text-white hover:bg-red-500 active:translate-x-[2px] active:translate-y-[2px] active:shadow-none',
  ghost:
    'bg-transparent text-vanguard-text border-transparent shadow-none hover:bg-vanguard-surface hover:border-black hover:shadow-brutal-sm',
}

const sizes = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-7 py-3.5 text-base',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  className,
  disabled,
  ...props
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={clsx(
        'inline-flex items-center justify-center gap-2',
        'font-bold uppercase tracking-wider',
        'border-3 border-black rounded-none',
        'shadow-brutal',
        'transition-all duration-200 ease-out',
        'cursor-pointer select-none',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-x-0 disabled:hover:translate-y-0 disabled:active:translate-x-0 disabled:active:translate-y-0',
        'hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-brutal-lg',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}