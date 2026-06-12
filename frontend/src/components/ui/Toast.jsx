export default function Toast({ message, type = "info" }) {
  const styles = {
    info: "border-vanguard-accent text-vanguard-accent",
    success: "border-vanguard-accent text-vanguard-accent",
    warning: "border-vanguard-warning text-vanguard-warning",
    danger: "border-vanguard-danger text-vanguard-danger",
  };

  if (!message) {
    return null;
  }

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 border-4 bg-vanguard-surface px-5 py-4 font-bold shadow-brutal-lg ${styles[type]}`}
    >
      {message}
    </div>
  );
}