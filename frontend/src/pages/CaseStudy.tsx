import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Clock3,
  Database,
  Layers,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { apiBase } from "../api";
import type { Study } from "../types";
import {
  ComparisonChart,
  DemandHeatmap,
  LearningChart,
} from "../components/Charts";
import BusinessValue from "../components/BusinessValue";

const chapters = [
  ["problem", "The business problem"],
  ["data", "Understand the data"],
  ["explore", "Find the patterns"],
  ["features", "Build honest features"],
  ["models", "Choose the model"],
  ["tuning", "Tune & validate"],
  ["results", "Measure the outcome"],
  ["impact", "Connect to business value"],
];

function ChapterHeading({
  number,
  label,
  title,
  children,
}: {
  number: string;
  label: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="chapter-heading">
      <span className="eyebrow">
        {number} / {label}
      </span>
      <h2>{title}</h2>
      <p>{children}</p>
    </div>
  );
}

export default function CaseStudy({
  study,
  openForecast,
}: {
  study: Study;
  openForecast: () => void;
}) {
  const [active, setActive] = useState("problem");
  const selected = study.final.find(
    (item) => item.model === "hist_gradient_boosting",
  )!;
  const weekly = study.final.find((item) => item.model === "seasonal_naive")!;
  const improvement = (1 - selected.mae / weekly.mae) * 100;
  const tuned = study.validation.find(
    (item) => item.configuration === "selected_grid_configuration",
  )!;
  const untuned = study.validation.find(
    (item) => item.configuration === "untuned_full_features",
  )!;
  const tuningImprovement = (1 - tuned.mae / untuned.mae) * 100;
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting);
        if (visible.length) setActive(visible[0].target.id);
      },
      { rootMargin: "-15% 0px -65% 0px" },
    );
    document
      .querySelectorAll(".chapter")
      .forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <section className="ride-hero">
        <img
          className="ride-hero-image"
          src={`${import.meta.env.BASE_URL}images/city-commute.jpg`}
          alt="Cyclists commuting together along a city bike lane"
          fetchPriority="high"
        />
        <div className="ride-hero-shade" />
        <div className="hero-copy">
          <span className="eyebrow">
            <span className="status-dot" /> URBAN MOBILITY / MACHINE LEARNING
          </span>
          <h1>
            The city moves.
            <br />
            <em>Stay ahead.</em>
          </h1>
          <p>
            Rush hour waits for no one. A next-hour bike demand forecast built
            from real data, honest experiments and a little forward thinking.
          </p>
          <div className="hero-actions">
            <button className="button primary" onClick={openForecast}>
              Take it for a spin <ArrowUpRight size={18} />
            </button>
            <a className="hero-story-link" href="#problem">
              Behind the forecast <ArrowRight size={17} />
            </a>
          </div>
        </div>
        <div className="hero-side-label">LESS GUESSWORK. MORE MOMENTUM.</div>
        <span className="photo-note">
          Urban cycling photography · illustrative
        </span>
        <div className="hero-bottom-line">
          <span>01 / THE NEXT HOUR STARTS HERE</span>
          <span>PYTHON + SCIKIT-LEARN + FASTAPI</span>
        </div>
      </section>
      <section
        className="ride-metrics"
        aria-label="Measured final evaluation results"
      >
        <div className="metric-intro">
          <span>
            BUILT TO BE
            <br />
            PUT TO THE TEST.
          </span>
          <ArrowUpRight size={30} />
        </div>
        <div>
          <strong>
            {selected.mae.toFixed(1)}
            <span> rentals</span>
          </strong>
          <p>average hourly prediction error</p>
        </div>
        <div>
          <strong>
            {improvement.toFixed(1)}
            <span>%</span>
          </strong>
          <p>lower error than the weekly baseline</p>
        </div>
        <div>
          <strong>
            {study.coverage.scored_hours.toLocaleString()}
            <span> hours</span>
          </strong>
          <p>scored on the final holdout</p>
        </div>
      </section>
      <section
        className="street-story"
        aria-label="Bikes in everyday city life"
      >
        <div className="street-copy">
          <span className="eyebrow">REAL STREETS. REAL RIDES.</span>
          <h2>
            Every number
            <br />
            has a journey
            <br />
            <em>behind it.</em>
          </h2>
          <p>
            A morning commute. An afternoon detour. Getting the next hour right
            starts with understanding how a city actually moves.
          </p>
          <a href="#problem" className="text-link">
            Follow the project <ArrowRight size={17} />
          </a>
        </div>
        <figure className="street-photo parked-photo">
          <img
            src={`${import.meta.env.BASE_URL}images/parked-bikes.jpg`}
            alt="Rows of everyday bicycles parked beside a city street"
            loading="lazy"
          />
          <figcaption>01 / Waiting for the next ride.</figcaption>
        </figure>
        <figure className="street-photo rider-photo">
          <img
            src={`${import.meta.env.BASE_URL}images/street-rider.jpg`}
            alt="A cyclist riding through a street lined with city buildings"
            loading="lazy"
          />
          <figcaption>02 / A city in motion.</figcaption>
        </figure>
      </section>

      <div className="study-layout">
        <aside className="chapter-nav">
          <span className="eyebrow">THE PROJECT, STEP BY STEP</span>
          <nav aria-label="Case study chapters">
            {chapters.map(([id, label], index) => (
              <a
                className={active === id ? "active" : ""}
                href={`#${id}`}
                key={id}
              >
                <span>{String(index + 1).padStart(2, "0")}</span>
                {label}
              </a>
            ))}
          </nav>
          <div className="sidebar-note">
            <ShieldCheck size={19} />
            <p>
              Measured results.
              <br />
              Clear assumptions.
              <br />
              Reproducible process.
            </p>
          </div>
        </aside>
        <main className="chapters">
          <section id="problem" className="chapter">
            <ChapterHeading
              number="01"
              label="THE BUSINESS PROBLEM"
              title="Demand changes. Planning needs to keep up."
            >
              A bike-sharing operator needs a better view of the next hour to
              support staffing and operational planning.
            </ChapterHeading>
            <div className="two-cards">
              <article className="info-card">
                <Clock3 />
                <h3>The planning challenge</h3>
                <p>
                  Commute peaks, weekends and seasonal changes make a single
                  average unreliable. Too little capacity can mean missed trips;
                  too much can mean idle resources.
                </p>
              </article>
              <article className="info-card">
                <TrendingUp />
                <h3>The ML objective</h3>
                <p>
                  Predict total rentals in the next hour using information
                  already available. Beat a simple previous-week forecast on a
                  chronological holdout.
                </p>
              </article>
            </div>
            <div className="callout">
              <strong>Business scenario, public-data project.</strong> This is a
              portfolio case study, not a commissioned client engagement.
              Station-level availability and financial outcomes are outside this
              dataset.
            </div>
          </section>

          <section id="data" className="chapter">
            <ChapterHeading
              number="02"
              label="UNDERSTAND THE DATA"
              title="Start with the timeline, not the algorithm."
            >
              UCI Bike Sharing records system-wide Capital Bikeshare demand in
              2011–2012. The hourly file matches a one-hour prediction horizon.
            </ChapterHeading>
            <div className="mini-metrics">
              <div>
                <Database size={17} />
                <strong>{study.data.observed_rows.toLocaleString()}</strong>
                <span>observed hours</span>
              </div>
              <div>
                <Clock3 size={17} />
                <strong>2 years</strong>
                <span>historical coverage</span>
              </div>
              <div>
                <Layers size={17} />
                <strong>{study.data.missing_timestamps}</strong>
                <span>absent timestamps</span>
              </div>
            </div>
            <div className="timeline-card">
              <h3>A split that respects time</h3>
              <div className="time-split">
                <span>Development · train + validate</span>
                <span>Final test · 90 days</span>
              </div>
              <div className="timeline-labels">
                <span>Jan 2011</span>
                <span>3 Oct 2012</span>
                <span>31 Dec 2012</span>
              </div>
              <p>
                The final period was held out during exploration and parameter
                selection. Missing hours are restored to the grid and kept
                unknown, rather than treated as zero rentals.
              </p>
            </div>
            <details>
              <summary>Why missing hours matter</summary>
              <p>
                Shifting 24 CSV rows does not necessarily mean 24 elapsed hours.
                A complete hourly index makes lag 24 refer to yesterday at the
                same time, even across gaps.
              </p>
            </details>
          </section>

          <section id="explore" className="chapter">
            <ChapterHeading
              number="03"
              label="FIND THE PATTERNS"
              title="The data has a daily rhythm."
            >
              Exploration uses only pre-test observations. Weekday commute peaks
              and broader weekend afternoons suggest that hour and day type
              should work together.
            </ChapterHeading>
            <article className="chart-card">
              <div className="chart-title">
                <div>
                  <h3>When people ride</h3>
                  <p>Mean hourly rentals by weekday · pre-test data</p>
                </div>
                <span className="small-tag">EDA</span>
              </div>
              <DemandHeatmap data={study.heatmap} />
              <div className="chart-insight">
                <ArrowUpRight size={17} />
                <span>
                  Strong weekday peaks around 08:00 and 17:00–18:00; weekends
                  shift toward midday.
                </span>
              </div>
            </article>
            <details className="figure-disclosure">
              <summary>
                Explore temperature, demand and weather correlations
              </summary>
              <img
                loading="lazy"
                src={`${apiBase}/figures/03_temperature_patterns.png`}
                alt="Temperature by month and hour, alongside observed temperature versus demand"
              />
              <img
                loading="lazy"
                src={`${apiBase}/figures/04_profiles_and_correlations.png`}
                alt="Working-day demand profiles and weather correlation matrix"
              />
              <p>
                Temperature is associated with demand, but the forecast cannot
                use future observed weather. The source documentation disagrees
                on Celsius conversion, so normalized temperature is retained.
                Correlation does not establish causation.
              </p>
            </details>
          </section>

          <section id="features" className="chapter">
            <ChapterHeading
              number="04"
              label="BUILD HONEST FEATURES"
              title="Useful information. Available on time."
            >
              The prediction is made after hour t closes, for hour t+1. Every
              historical feature stops before the target hour.
            </ChapterHeading>
            <div className="feature-flow">
              <div>
                <span>KNOWN IN ADVANCE</span>
                <strong>Calendar</strong>
                <p>
                  Hour · weekday · month
                  <br />
                  Holiday · working day
                  <br />
                  Cyclical encodings
                </p>
              </div>
              <ArrowRight />
              <div>
                <span>ALREADY OBSERVED</span>
                <strong>Demand history</strong>
                <p>
                  Lags 1, 2, 24, 48, 168h
                  <br />
                  Shifted 24h / 168h mean
                  <br />
                  Historical variability
                </p>
              </div>
              <ArrowRight />
              <div className="target-block">
                <span>THE TARGET</span>
                <strong>Next hour</strong>
                <p>
                  Total rental count
                  <br />
                  <code>cnt(t + 1)</code>
                </p>
              </div>
            </div>
            <div className="callout">
              <ShieldCheck size={19} />
              <p>
                <strong>Leakage checks are part of the model.</strong> Casual
                and registered rentals are excluded because they sum to the
                target. Future observed weather is excluded. Tests change future
                demand and verify that earlier features stay the same.
              </p>
            </div>
            <details>
              <summary>One saved pipeline, from history to prediction</summary>
              <div className="code-flow">
                history → features → feature selection → preprocessing → HGB →
                nonnegative count
              </div>
              <p>
                Numeric medians, scaling and one-hot categories are fitted
                inside each training fold. The API uses that same saved
                pipeline; it does not recreate feature logic in another
                language.
              </p>
            </details>
          </section>

          <section id="models" className="chapter">
            <ChapterHeading
              number="05"
              label="CHOOSE THE MODEL"
              title="Make the model earn its complexity."
            >
              The initial experiment compared two simple rules, a linear
              regressor and two tree ensembles on the same expanding validation
              folds.
            </ChapterHeading>
            <article className="chart-card">
              <div className="chart-title">
                <div>
                  <h3>The first comparison</h3>
                  <p>Mean validation MAE · original fixed settings</p>
                </div>
                <span className="small-tag">LOWER IS BETTER</span>
              </div>
              <ComparisonChart data={study.initial_comparison} />
              <p className="chart-caption">
                Gradient boosting led all three folds. The current application
                serves this one selected algorithm; these earlier results
                explain the choice.
              </p>
            </article>
            <div className="two-cards">
              <div className="small-card">
                <strong>Expanding-window validation</strong>
                <p>
                  Train on earlier hours, validate on the following 28 days,
                  then expand the training window. No random train/test shuffle.
                </p>
              </div>
              <div className="small-card">
                <strong>Rolling one-hour ahead</strong>
                <p>
                  Each later forecast can use newly observed demand. This
                  differs from predicting an entire month from one starting
                  point.
                </p>
              </div>
            </div>
          </section>

          <section id="tuning" className="chapter">
            <ChapterHeading
              number="06"
              label="TUNE & VALIDATE"
              title="A small search. An honest improvement."
            >
              GridSearchCV evaluated 32 configurations over three expanding
              folds: 96 fits. Selection minimized mean absolute error, with
              preprocessing inside the pipeline.
            </ChapterHeading>
            <div className="tuning-result">
              <div>
                <span>UNTUNED CV MAE</span>
                <strong>{untuned.mae.toFixed(2)}</strong>
              </div>
              <ArrowRight />
              <div>
                <span>SELECTED CV MAE</span>
                <strong>{tuned.mae.toFixed(2)}</strong>
              </div>
              <span className="improvement-pill">
                {tuningImprovement.toFixed(2)}% lower
              </span>
            </div>
            <div className="parameter-grid">
              {[
                ["Learning rate", study.selection.regressor__learning_rate],
                ["Boosting iterations", study.selection.regressor__max_iter],
                ["Maximum leaves", study.selection.regressor__max_leaf_nodes],
                [
                  "L2 regularization",
                  study.selection.regressor__l2_regularization,
                ],
              ].map(([label, value]) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
            <article className="chart-card">
              <div className="chart-title">
                <div>
                  <h3>How the model learned</h3>
                  <p>MAE after each added tree · mean of three folds</p>
                </div>
              </div>
              <LearningChart data={study.learning} />
              <p className="chart-caption">
                Training error keeps falling while validation improvement
                flattens. We track both; training fit alone does not establish
                future performance. These folds were also used for parameter
                selection.
              </p>
            </article>
            <details>
              <summary>Inspect the top grid-search candidates</summary>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Rate</th>
                      <th>Trees</th>
                      <th>Leaves</th>
                      <th>L2</th>
                      <th>Rolling</th>
                      <th>CV MAE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {study.candidates.map((row, index) => (
                      <tr key={index}>
                        <td>{row.rank_test_score}</td>
                        <td>{row.param_regressor__learning_rate}</td>
                        <td>{row.param_regressor__max_iter}</td>
                        <td>{row.param_regressor__max_leaf_nodes}</td>
                        <td>{row.param_regressor__l2_regularization}</td>
                        <td>
                          {row.param_select__feature_set ===
                          "calendar_and_history"
                            ? "Included"
                            : "Excluded"}
                        </td>
                        <td>{row.mean_validation_mae.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p>
                The selected feature set retained the rolling summaries. The
                test period was not part of this search.
              </p>
            </details>
          </section>

          <section id="results" className="chapter">
            <ChapterHeading
              number="07"
              label="MEASURE THE OUTCOME"
              title="Then ask the future to judge it."
            >
              After freezing the choices, the saved model was evaluated on
              October–December 2012 without fitting or tuning.
            </ChapterHeading>
            <div className="result-grid">
              <div>
                <span>FINAL TEST MAE</span>
                <strong>{selected.mae.toFixed(2)}</strong>
                <p>rentals / hour</p>
              </div>
              <div>
                <span>WITHIN ±50 RENTALS</span>
                <strong>{selected.within_50_rentals_pct.toFixed(1)}%</strong>
                <p>of scored predictions</p>
              </div>
              <div>
                <span>WITHIN ±20% OF ACTUAL</span>
                <strong>{selected.within_20_percent_pct.toFixed(1)}%</strong>
                <p>of scored predictions</p>
              </div>
            </div>
            <article className="chart-card">
              <div className="chart-title">
                <div>
                  <h3>Actual demand meets the forecast</h3>
                  <p>
                    First seven test days · selected by date, not performance
                  </p>
                </div>
              </div>
              <img
                className="result-figure"
                loading="lazy"
                src={`${apiBase}/figures/09_final_test_predictions.png`}
                alt="Actual versus predicted demand during the first week of the final test"
              />
            </article>
            <div className="table-scroll results-table">
              <table>
                <thead>
                  <tr>
                    <th>Final-test predictor</th>
                    <th>MAE ↓</th>
                    <th>RMSE ↓</th>
                    <th>R² ↑</th>
                  </tr>
                </thead>
                <tbody>
                  {study.final.map((row) => (
                    <tr key={row.model}>
                      <td>
                        {row.model === "hist_gradient_boosting"
                          ? "Selected gradient boosting"
                          : row.model === "seasonal_naive"
                            ? "Same hour previous week"
                            : "Previous hour"}
                      </td>
                      <td>{row.mae.toFixed(2)}</td>
                      <td>{row.rmse.toFixed(2)}</td>
                      <td>{row.r2.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="footnote">
              Scored {study.coverage.scored_hours.toLocaleString()} /{" "}
              {study.coverage.observed_target_hours.toLocaleString()} observed
              hours (
              {(study.coverage.scored_fraction_of_observed * 100).toFixed(2)}%).
              Missing recent or weekly history excludes an hour for every
              predictor. R² is not an accuracy percentage. This holdout is now
              used and stays out of future tuning decisions.
            </p>
          </section>

          <section id="impact" className="chapter">
            <ChapterHeading
              number="08"
              label="CONNECT TO BUSINESS VALUE"
              title="Better forecasts are a starting point for better decisions."
            >
              The measured outcome is lower forecast error. Financial value
              would need an operational trial with real costs, decisions and
              outcomes.
            </ChapterHeading>
            <div className="outcome-list">
              {[
                `${improvement.toFixed(1)}% lower final-test MAE than the previous-week rule`,
                "A reproducible pipeline with the same features in training and serving",
                "Clear errors, coverage and limitations rather than a single accuracy claim",
              ].map((item) => (
                <div key={item}>
                  <Check size={18} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
            <BusinessValue />
            <div className="closing-card">
              <div>
                <span className="eyebrow">FROM EXPERIMENT TO APPLICATION</span>
                <h3>See the model make a prediction.</h3>
                <p>
                  Replay a historical hour with real observed history and
                  compare its forecast with what happened.
                </p>
              </div>
              <button className="button primary" onClick={openForecast}>
                Open forecast lab <ArrowUpRight size={17} />
              </button>
            </div>
            <details>
              <summary>What this project does not establish</summary>
              <p>
                Generalization to another city or current demand, station-level
                bike allocation, causal weather effects, prediction intervals
                and measured client profit have not been established. The data
                is historical and assumes immediate availability of
                completed-hour counts.
              </p>
            </details>
          </section>
        </main>
      </div>
    </>
  );
}
