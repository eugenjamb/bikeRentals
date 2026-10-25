import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import type { Study } from "../types";

const labels: Record<string, string> = {
  hist_gradient_boosting: "Gradient boosting",
  random_forest: "Random Forest",
  ridge: "Ridge regression",
  seasonal_naive: "Previous week",
  last_hour: "Previous hour",
};

export function ComparisonChart({
  data,
}: {
  data: { model: string; mae: number }[];
}) {
  const rows = data.map((row) => ({ ...row, label: labels[row.model] }));
  return (
    <div className="chart" aria-label="Model comparison: lower MAE is better">
      <ResponsiveContainer width="100%" height={255}>
        <BarChart data={rows} layout="vertical" margin={{ left: 5, right: 28 }}>
          <CartesianGrid horizontal={false} stroke="#e6e1d8" />
          <XAxis
            type="number"
            axisLine={false}
            tickLine={false}
            fontSize={11}
          />
          <YAxis
            type="category"
            dataKey="label"
            width={126}
            axisLine={false}
            tickLine={false}
            fontSize={12}
          />
          <Tooltip
            formatter={(value) => [
              Number(value).toFixed(2),
              "MAE · rentals/hour",
            ]}
            cursor={{ fill: "#f3eee6" }}
          />
          <Bar
            dataKey="mae"
            radius={[0, 4, 4, 0]}
            barSize={23}
            isAnimationActive={false}
          >
            {rows.map((row) => (
              <Cell
                key={row.model}
                fill={
                  row.model === "hist_gradient_boosting" ? "#242424" : "#bcb6ac"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LearningChart({ data }: { data: Study["learning"] }) {
  return (
    <div
      className="chart"
      aria-label="Training and validation error by boosting iteration"
    >
      <ResponsiveContainer width="100%" height={270}>
        <LineChart data={data} margin={{ left: -18, right: 12, bottom: 5 }}>
          <CartesianGrid
            strokeDasharray="3 4"
            vertical={false}
            stroke="#e6e1d8"
          />
          <XAxis
            dataKey="iteration"
            axisLine={false}
            tickLine={false}
            fontSize={11}
            minTickGap={30}
          />
          <YAxis axisLine={false} tickLine={false} fontSize={11} />
          <Tooltip
            labelFormatter={(value) => `Iteration ${value}`}
            formatter={(value) => Number(value).toFixed(2)}
          />
          <Line
            type="monotone"
            dataKey="training_mae"
            name="Training MAE"
            stroke="#242424"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="validation_mae"
            name="Validation MAE"
            stroke="#f45b2a"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="chart-key">
        <span>
          <i className="ink-dot" />
          Training
        </span>
        <span>
          <i className="orange-dot" />
          Validation
        </span>
        <span>Lower is better · rentals/hour</span>
      </div>
    </div>
  );
}

export function HistoryChart({
  data,
}: {
  data: { hour: string; actual?: number | null; forecast?: number | null }[];
}) {
  return (
    <div
      className="chart"
      aria-label="Recent observed demand and the next-hour prediction"
    >
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ left: -12, right: 15 }}>
          <CartesianGrid
            strokeDasharray="3 4"
            vertical={false}
            stroke="#e6e1d8"
          />
          <XAxis
            dataKey="hour"
            axisLine={false}
            tickLine={false}
            fontSize={11}
            minTickGap={25}
          />
          <YAxis axisLine={false} tickLine={false} fontSize={11} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="actual"
            name="Observed"
            stroke="#242424"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            dataKey="forecast"
            name="Forecast"
            stroke="#f45b2a"
            strokeWidth={2.5}
            strokeDasharray="5 4"
            dot={{ r: 5, fill: "#f45b2a", stroke: "#fff", strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="chart-key">
        <span>
          <i className="ink-dot" />
          Observed history
        </span>
        <span>
          <i className="orange-dot" />
          Next-hour forecast
        </span>
      </div>
    </div>
  );
}

export function DemandHeatmap({ data }: { data: Study["heatmap"] }) {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const maximum = Math.max(...data.map((item) => item.demand));
  return (
    <div className="heatmap-wrap">
      <div
        className="heatmap"
        role="img"
        aria-label="Average demand heatmap: weekday commute peaks and weekend midday demand"
      >
        <span />
        {Array.from({ length: 24 }, (_, hour) => (
          <span className="heat-hour" key={hour}>
            {hour % 3 === 0 ? hour.toString().padStart(2, "0") : ""}
          </span>
        ))}
        {days.map((day, weekday) => (
          <div className="heat-row" key={day}>
            <span className="heat-day">{day}</span>
            {Array.from({ length: 24 }, (_, hour) => {
              const value =
                data.find(
                  (item) => item.weekday === weekday && item.hour === hour,
                )?.demand ?? 0;
              return (
                <span
                  key={hour}
                  className="heat-cell"
                  tabIndex={0}
                  title={`${day}, ${hour}:00 · ${value.toFixed(0)} mean rentals`}
                  style={{
                    background: `color-mix(in srgb, #e9582a ${12 + (value / maximum) * 88}%, #f5ede0)`,
                  }}
                />
              );
            })}
          </div>
        ))}
      </div>
      <div className="heat-legend">
        <span>Less demand</span>
        <i />
        <span>More demand</span>
      </div>
    </div>
  );
}
