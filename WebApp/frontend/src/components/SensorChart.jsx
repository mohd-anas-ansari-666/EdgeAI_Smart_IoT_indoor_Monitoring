// src/components/SensorChart.jsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function SensorChart({ data, dataKey, label, color }) {
  // Format data for chart
  const formattedData = data.map(item => ({
    ...item,
    timestamp: new Date(item.timestamp).toLocaleTimeString()
  }));
  
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={formattedData}
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey={dataKey} stroke={color} activeDot={{ r: 8 }} />
        </LineChart>
      </ResponsiveContainer>
      <div className="text-center mt-2 font-medium text-gray-600">{label}</div>
    </div>
  );
}

export default SensorChart;