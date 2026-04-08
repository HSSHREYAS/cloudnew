import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function ComparisonChart({ data }) {
  if (!data?.length) {
    return <div className="empty-chart">Comparison results will appear here.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="region" />
        <YAxis />
        <Tooltip formatter={(value) => [`$${Number(value).toFixed(4)}`, "Projected cost"]} />
        <Bar dataKey="total_cost" fill="#0f6d64" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

