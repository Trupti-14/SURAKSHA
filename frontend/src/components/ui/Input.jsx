export default function Input({ label, error, className = "", ...props }) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-2 block text-sm font-bold text-vanguard-muted">
          {label}
        </label>
      )}

      <input
        className={`w-full border-2 border-black bg-vanguard-surface px-4 py-3 text-vanguard-text outline-none shadow-brutal-sm focus:border-vanguard-accent ${className}`}
        {...props}
      />

      {error && <p className="mt-2 text-sm text-vanguard-danger">{error}</p>}
    </div>
  );
}