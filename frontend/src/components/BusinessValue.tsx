import { useState } from "react";
import { ArrowUpRight } from "lucide-react";

export default function BusinessValue() {
  const [decisions, setDecisions] = useState(4);
  const [minutes, setMinutes] = useState(5);
  const [rate, setRate] = useState(30);
  const hours = (decisions * minutes * 30) / 60;
  const money = hours * rate;
  return (
    <div className="value-panel">
      <div>
        <span className="eyebrow">EXPLORE A BUSINESS SCENARIO</span>
        <h3>What could better planning be worth?</h3>
        <p>
          Estimate the value of staff time saved if a forecasting tool reduces
          manual planning. Adjust the assumptions.
        </p>
        <div className="value-inputs">
          <label>
            Planning decisions / day
            <input
              type="number"
              min="0"
              max="100"
              value={decisions}
              onChange={(event) =>
                setDecisions(
                  Math.max(0, Math.min(100, Number(event.target.value))),
                )
              }
            />
          </label>
          <label>
            Minutes saved / decision
            <input
              type="number"
              min="0"
              max="120"
              value={minutes}
              onChange={(event) =>
                setMinutes(
                  Math.max(0, Math.min(120, Number(event.target.value))),
                )
              }
            />
          </label>
          <label>
            Staff cost / hour ($)
            <input
              type="number"
              min="0"
              max="500"
              value={rate}
              onChange={(event) =>
                setRate(Math.max(0, Math.min(500, Number(event.target.value))))
              }
            />
          </label>
        </div>
      </div>
      <div className="value-result">
        <ArrowUpRight size={26} />
        <span>Illustrative monthly time value</span>
        <strong>
          ${money.toLocaleString("en-US", { maximumFractionDigits: 0 })}
        </strong>
        <p>{hours.toFixed(1)} hours over 30 days</p>
        <small>
          Assumption-based scenario. No client profit, time savings or revenue
          lift has been measured.
        </small>
      </div>
    </div>
  );
}
