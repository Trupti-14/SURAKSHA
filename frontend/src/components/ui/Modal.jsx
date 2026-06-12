export default function Modal({ open, title, children, onClose }) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-lg border-4 border-black bg-vanguard-surface p-6 shadow-brutal-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-black text-vanguard-text">{title}</h2>

          <button
            onClick={onClose}
            className="border-2 border-black bg-vanguard-danger px-3 py-1 font-black text-white shadow-brutal-sm"
          >
            X
          </button>
        </div>

        {children}
      </div>
    </div>
  );
}