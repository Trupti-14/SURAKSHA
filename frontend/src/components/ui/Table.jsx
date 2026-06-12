export default function Table({ columns = [], data = [] }) {
  return (
    <div className="overflow-x-auto border-2 border-black shadow-brutal-sm">
      <table className="w-full border-collapse bg-vanguard-surface text-left">
        <thead className="bg-black text-vanguard-accent">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className="px-4 py-3 text-sm font-black">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {data.map((row, index) => (
            <tr key={index} className="border-t border-black">
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 text-sm">
                  {row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}