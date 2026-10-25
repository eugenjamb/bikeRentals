import { useEffect, useState } from "react";
import { ArrowUpRight, Bike, LoaderCircle } from "lucide-react";
import { getStudy } from "./api";
import type { Study } from "./types";
import CaseStudy from "./pages/CaseStudy";
import ForecastLab from "./pages/ForecastLab";

export default function App() {
  const [view, setView] = useState<"story" | "forecast">(() =>
    new URLSearchParams(window.location.search).get("view") === "forecast"
      ? "forecast"
      : "story",
  );
  const [study, setStudy] = useState<Study | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getStudy()
      .then(setStudy)
      .catch((error) => setError(error.message));
  }, []);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [view]);
  function navigate(next: "story" | "forecast") {
    setView(next);
    const url = new URL(window.location.href);
    url.search = next === "forecast" ? "?view=forecast" : "";
    url.hash = "";
    window.history.replaceState({}, "", url);
  }
  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <header className="site-header">
        <div className="header-inner">
          <button
            className="brand"
            aria-label="Cyclecast home"
            onClick={() => navigate("story")}
          >
            <span className="brand-icon">
              <Bike size={23} strokeWidth={1.8} />
            </span>
            <strong>
              cyclecast<span>.</span>
            </strong>
            <span className="brand-caption">DEMAND, UNDERSTOOD.</span>
          </button>
          <nav className="view-tabs" aria-label="Project views">
            <button
              aria-current={view === "story" ? "page" : undefined}
              className={view === "story" ? "active" : ""}
              onClick={() => navigate("story")}
            >
              The case study
            </button>
            <button
              aria-current={view === "forecast" ? "page" : undefined}
              className={view === "forecast" ? "active" : ""}
              onClick={() => navigate("forecast")}
            >
              Forecast lab <ArrowUpRight size={14} />
            </button>
          </nav>
          <a
            className="source-link"
            href="https://github.com/eugenjamb/bikeRentals"
            target="_blank"
            rel="noreferrer"
          >
            View source <ArrowUpRight size={14} />
          </a>
        </div>
      </header>
      <div className="site-body" id="main-content">
        {error ? (
          <div className="app-state error-box" role="alert">
            <h1>The project could not load</h1>
            <p>{error}</p>
            <button
              className="button primary"
              onClick={() => window.location.reload()}
            >
              Try again
            </button>
          </div>
        ) : !study ? (
          <div className="app-state">
            <LoaderCircle size={24} className="spin" />
            <p>Loading the project…</p>
          </div>
        ) : view === "story" ? (
          <CaseStudy study={study} openForecast={() => navigate("forecast")} />
        ) : (
          <ForecastLab />
        )}
      </div>
      <footer className="site-footer">
        <div>
          <Bike size={18} />
          <strong>cyclecast.</strong>
          <span>A machine learning portfolio project.</span>
        </div>
        <p>
          Data:{" "}
          <a
            href="https://doi.org/10.24432/C5W894"
            target="_blank"
            rel="noreferrer"
          >
            UCI Bike Sharing · Hadi Fanaee-T
          </a>{" "}
          · CC BY 4.0
          <br />
          Urban cycling photography:{" "}
          <a href="https://unsplash.com" target="_blank" rel="noreferrer">
            Unsplash
          </a>
        </p>
      </footer>
    </>
  );
}
