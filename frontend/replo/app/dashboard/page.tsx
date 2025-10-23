export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border rounded p-4">
          <h2 className="font-semibold mb-2">Overview</h2>
          <p className="text-sm text-gray-600">Quick stats and summaries.</p>
        </div>
        <div className="border rounded p-4">
          <h2 className="font-semibold mb-2">Recent Activity</h2>
          <p className="text-sm text-gray-600">Latest changes and updates.</p>
        </div>
      </div>
    </div>
  );
}