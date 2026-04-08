import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#0f6d64", "#f4b942", "#de6b48", "#2f3c7e"];

export default function CostBreakdownChart({ data }) {
  if (!data?.length) {
    return <div className="empty-chart">Run an estimate to see the cost composition.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          dataKey="amount"
          nameKey="label"
          innerRadius={70}
          outerRadius={100}
          paddingAngle={4}
        >
          {data.map((entry, index) => (
            <Cell key={entry.label} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => [`$${Number(value).toFixed(4)}`, "Cost"]} />
      </PieChart>
    </ResponsiveContainer>
  );
}

