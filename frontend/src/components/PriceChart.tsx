export function PriceChart() {
  // Mock data for MVP - price history not yet implemented
  const mockData = [
    { date: 'Jan', value: 8500 },
    { date: 'Feb', value: 9200 },
    { date: 'Mar', value: 9800 },
    { date: 'Apr', value: 10500 },
    { date: 'May', value: 11200 },
    { date: 'Jun', value: 12100 },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Collection Value Over Time</h2>
      
      {/* Placeholder for chart */}
      <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-700/50 rounded border-2 border-dashed border-gray-300 dark:border-gray-600">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-2">📊 Price History Coming Soon</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">Historical price tracking will be available in a future update</p>
        </div>
      </div>
      
      {/* Mock data display */}
      <div className="mt-4 grid grid-cols-6 gap-2 text-xs text-center">
        {mockData.map((item) => (
          <div key={item.date} className="text-gray-600 dark:text-gray-400">
            <div className="font-medium">{item.date}</div>
            <div className="text-green-600 dark:text-green-400">€{item.value.toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
