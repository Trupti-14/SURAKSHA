export default function ProgressBar({ value = 0 }) {
  const safeValue = Math.min(100, Math.max(0, value));

  return (
    <div className="h-4 w-full border-2 border-black bg-vanguard-bg">
      <div
        className="h-full bg-vanguard-accent transition-all duration-300"
        style={{ width: `${safeValue}%` }}
      />
    </div>
  );
}