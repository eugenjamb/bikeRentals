import { useEffect, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Clock3,
  Code2,
  LoaderCircle,
  Play,
  RotateCcw,
} from "lucide-react";
import { getScenario, getScenarios, predict } from "../api";
import type { Forecast, ForecastRequest, Scenario } from "../types";
import { HistoryChart } from "../components/Charts";

export default function ForecastLab() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState<Scenario | null>(null);
  const [result, setResult] = useState<Forecast | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [custom, setCustom] = useState(false);
  const [payload, setPayload] = useState("");

  async function choose(id: string) {
    setLoading(true);
    setError("");
    setResult(null);
    setCustom(false);
    try {
      const scenario = await getScenario(id);
      setSelected(scenario);
      setPayload(JSON.stringify(scenario.request, null, 2));
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    getScenarios()
      .then((items) => {
        if (cancelled) return;
        setScenarios(items);
        if (items.length) void choose(items[0].id);
        else setLoading(false);
      })
      .catch((error) => {
        if (!cancelled) {
          setError(error.message);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function runPrediction() {
    setBusy(true);
    setError("");
    try {
      const request = (
        custom ? JSON.parse(payload) : selected?.request
      ) as ForecastRequest;
      if (!request) throw new Error("Choose a scenario first.");
      setResult(await predict(request));
    } catch (error) {
      setError((error as Error).message);
      setResult(null);
    } finally {
      setBusy(false);
    }
  }

  const request = selected?.request;
  const history =
    request?.history
      .slice(-24)
      .map((item) => ({
        hour: item.timestamp.slice(11, 16),
        actual: item.count,
        forecast: null as number | null,
      })) ?? [];
  if (result && !custom) {
    if (history.length)
      history[history.length - 1].forecast = history[history.length - 1].actual;
    history.push({
      hour: result.target_timestamp.slice(11, 16),
      actual: null,
      forecast: result.predicted_rentals,
    });
  }
  const errorCount =
    result && selected
      ? Math.abs(result.predicted_rentals - selected.actual)
      : 0;
  return (
    <main className="lab-page">
      <div className="lab-heading">
        <span className="eyebrow">
          <span className="status-dot" /> INTERACTIVE MODEL DEMO
        </span>
        <h1>One hour. A real prediction.</h1>
        <p>
          Choose a historical scenario. The API uses only the preceding week of
          observations to forecast the next hour.
        </p>
      </div>
      <div className="replay-notice">
        <Clock3 size={17} />
        <span>
          Historical replay · Capital Bikeshare, 2012. These examples are from
          the final test period; this is not a live demand service.
        </span>
      </div>
      <div className="lab-grid">
        <section className="scenario-panel">
          <div className="panel-title">
            <span className="eyebrow">01 / CHOOSE THE CONTEXT</span>
            <h2>Pick an hour to replay</h2>
          </div>
          <div
            className="scenario-list"
            role="group"
            aria-label="Historical scenarios"
          >
            {scenarios.map((scenario) => (
              <button
                key={scenario.id}
                disabled={busy || loading}
                className={`scenario-option ${selected?.id === scenario.id ? "selected" : ""}`}
                onClick={() => void choose(scenario.id)}
              >
                <span className="radio-dot" />
                <div>
                  <strong>{scenario.label}</strong>
                  <span>{scenario.description}</span>
                </div>
                {selected?.id === scenario.id && <CheckCircle2 size={17} />}
              </button>
            ))}
          </div>
          {loading ? (
            <p className="loading-line">
              <LoaderCircle className="spin" size={16} /> Loading observed
              history…
            </p>
          ) : (
            request && (
              <div className="context-facts">
                <div>
                  <span>Target hour</span>
                  <strong>
                    {request.target_timestamp.replace("T", " ").slice(0, 16)}
                  </strong>
                </div>
                <div>
                  <span>Day type</span>
                  <strong>
                    {request.workingday ? "Working day" : "Weekend / holiday"}
                  </strong>
                </div>
                <div>
                  <span>History</span>
                  <strong>168 hourly positions</strong>
                </div>
                <div>
                  <span>Forecast horizon</span>
                  <strong>1 hour ahead</strong>
                </div>
              </div>
            )
          )}
          <button
            className="button primary predict-button"
            disabled={busy || loading || !selected}
            onClick={() => void runPrediction()}
          >
            {busy ? (
              <LoaderCircle size={17} className="spin" />
            ) : (
              <Play size={16} />
            )}
            {busy ? "Running the pipeline…" : "Predict next-hour demand"}
            {!busy && <ArrowRight size={17} />}
          </button>
          <details
            className="custom-payload"
            onToggle={(event) => {
              if (!(event.target as HTMLDetailsElement).open) {
                setCustom(false);
                setResult(null);
              }
            }}
          >
            <summary>
              <Code2 size={15} /> Developer mode: custom request
            </summary>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={custom}
                onChange={(event) => {
                  setCustom(event.target.checked);
                  setResult(null);
                }}
              />{" "}
              Use edited JSON instead of the selected scenario
            </label>
            <textarea
              aria-label="Custom prediction request JSON"
              value={payload}
              onChange={(event) => setPayload(event.target.value)}
              spellCheck={false}
            />
            <p>
              Exactly 168 ordered historical hours, ending before the target.
              Future observations and unknown fields are rejected. Custom
              requests are not compared with a scenario's actual demand.
            </p>
          </details>
        </section>
        <section className="forecast-panel">
          <div className="panel-title">
            <span className="eyebrow">02 / THE NEXT HOUR</span>
            <h2>{result ? "Your demand forecast" : "Ready when you are"}</h2>
          </div>
          {error && (
            <div className="error-box" role="alert">
              {error}
            </div>
          )}
          <div
            className={`prediction-card ${result ? "has-result" : ""}`}
            aria-live="polite"
          >
            <span>SYSTEM-WIDE RENTALS</span>
            <strong>
              {result ? result.display_rentals.toLocaleString() : "—"}
              <small>bikes / hour</small>
            </strong>
            <p>
              {result
                ? `For ${result.target_timestamp.replace("T", " ").slice(0, 16)}`
                : "Run the saved pipeline to see a forecast."}
            </p>
            {result && (
              <span className="latency">
                <CheckCircle2 size={14} /> Pipeline completed in{" "}
                {result.elapsed_ms.toFixed(1)} ms
              </span>
            )}
          </div>
          {result && !custom && selected && (
            <div className="replay-comparison">
              <div>
                <span>Actually observed</span>
                <strong>{selected.actual}</strong>
              </div>
              <div>
                <span>Absolute error</span>
                <strong>{errorCount.toFixed(1)}</strong>
              </div>
              <div>
                <span>Relative error</span>
                <strong>
                  {((errorCount / selected.actual) * 100).toFixed(1)}%
                </strong>
              </div>
            </div>
          )}
          {!custom && (
            <article className="history-card">
              <div className="chart-title">
                <div>
                  <h3>The history behind the forecast</h3>
                  <p>Last 24 of the 168 preceding hourly positions</p>
                </div>
              </div>
              <HistoryChart data={history} />
            </article>
          )}
          {result && (
            <button
              className="text-link reset-link"
              onClick={() => setResult(null)}
            >
              <RotateCcw size={14} /> Clear prediction
            </button>
          )}
        </section>
      </div>
      <div className="lab-footnote">
        <strong>What happens behind the button?</strong>
        <p>
          FastAPI validates the history → the saved pipeline builds calendar and
          historical features → it selects the trained feature set and applies
          preprocessing → gradient boosting predicts a nonnegative count. No
          retraining or grid search runs here.
        </p>
      </div>
    </main>
  );
}
