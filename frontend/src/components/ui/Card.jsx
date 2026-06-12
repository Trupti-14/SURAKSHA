import clsx from 'clsx'

export default function Card({
  children,
  title,
  subtitle,
  footer,
  className,
  headerClassName,
  bodyClassName,
  ...props
}) {
  return (
    <article
      className={clsx(
        'flex flex-col',
        'bg-vanguard-surface',
        'border-3 border-black',
        'shadow-brutal',
        'transition-all duration-200',
        'hover:shadow-brutal-lg hover:-translate-x-0.5 hover:-translate-y-0.5',
        className,
      )}
      {...props}
    >
      {(title || subtitle) && (
        <header
          className={clsx(
            'border-b-3 border-black px-6 py-4',
            headerClassName,
          )}
        >
          {title && (
            <h2 className="m-0 text-lg font-black uppercase tracking-wide text-vanguard-text">
              {title}
            </h2>
          )}
          {subtitle && (
            <p className="mt-1 mb-0 text-sm text-vanguard-muted">{subtitle}</p>
          )}
        </header>
      )}

      <div className={clsx('flex flex-1 flex-col px-6 py-5', bodyClassName)}>
        {children}
      </div>

      {footer && (
        <footer className="border-t-3 border-black px-6 py-4">{footer}</footer>
      )}
    </article>
  )
}