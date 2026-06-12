export default function Tabs({ tabs = [], activeTab, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onChange(tab.value)}
          className={`border-2 border-black px-4 py-2 font-black shadow-brutal-sm transition-all ${
            activeTab === tab.value
              ? "bg-vanguard-accent text-black"
              : "bg-vanguard-surface text-vanguard-text hover:bg-black"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}