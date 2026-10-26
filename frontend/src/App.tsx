import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  type DayList,
  type MetricsPayload,
  type Overview,
  type SeriesPoint,
} from "./api";

function fmtMw(n: number | null | undefined): string {
  if (n == null) return "—";
  return Math.round(n).toLocaleString("en-GB");
}

function shortTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/London",
  });
}

export default function App() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [metrics, setMetrics] = useState<MetricsPayload | null>(null);
  const [days, setDays] = useState<DayList["days"]>([]);
  const [day, setDay] = useState<string>("");
  const [series, setSeries] = useState<SeriesPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [ov, met, dayList] = await Promise.all([
          api.overview(),
          api.metrics(),
          api.days(),
        ]);
        if (cancelled) return;
        setOverview(ov);
        setMetrics(met);
        setDays(dayList.days);
        const pick =
          ov.latestDeliveryDay ??
          dayList.days.find((d) => d.withActual > 0)?.deliveryDay ??
          dayList.days[0]?.deliveryDay ??
          "";
        setDay(pick);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!day) return;
    let cancelled = false;
    (async () => {
      try {
        const [s, m] = await Promise.all([api.series(day), api.metrics(day)]);
        if (cancelled) return;
        setSeries(s.points);
        setMetrics((prev) =>
          prev
            ? {
                ...prev,
                overall: m.overall,
                byLeadHour: m.byLeadHour,
                byHourLocal: m.byHourLocal,
                errorHistogram: m.errorHistogram,
              }
            : m,
        );
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [day]);

  if (loading) {
    return (
      <div className="shell">
        <p className="loading">Loading January 2026 wind desk…</p>
      </div>
    );
  }

  if (error || !overview || !metrics) {
    return (
      <div className="shell">
        <p className="error">
          Could not reach the Boreas API ({error ?? "unknown"}). Start the
          backend on :8000 or use docker compose.
        </p>
      </div>
    );
  }

  const chartData = series.map((p) => ({
    t: shortTime(p.startTime),
    forecast: p.forecastMw,
    actual: p.actualMw,
    error: p.errorMw,
  }));

  const hist = metrics.errorHistogram.binCentersMw.map((c, i) => ({
    mw: c,
    count: metrics.errorHistogram.counts[i] ?? 0,
  }));

  return (
    <div className="shell">
      <header className="nav">
        <a className="brand" href="#top">
          Boreas
        </a>
        <nav className="nav-links">
          <a href="#desk">Desk view</a>
          <a href="#accuracy">Accuracy</a>
          <a href="#method">Method</a>
        </nav>
      </header>

      <main id="top">
        <section className="hero" aria-label="Hero">
          <p className="hero-brand">Boreas</p>
          <h2>Day-ahead wind you can buy against.</h2>
          <p>
            National GB wind forecasts as a trader would have seen them before
            the EPEX gate — paired with January 2026 actuals and a residual
            procurement band.
          </p>
          <div className="cta-row">
            <a className="btn btn-primary" href="#desk">
              Open the desk
            </a>
            <a className="btn btn-ghost" href="#method">
              Decision window
            </a>
          </div>
        </section>

        <section id="desk" aria-labelledby="desk-title">
          <p className="section-label">Trader desk · Jan 2026</p>
          <h3 id="desk-title">Forecast at the gate vs outturn</h3>
          <p className="lede">
            Each day uses the latest WINDFOR run published on or before 09:20
            CET on D−1 — not the look-ahead that arrives after you bid.
          </p>

          <div className="metric-strip">
            <div className="metric">
              <div className="label">MAE</div>
              <div className="value">
                {fmtMw(overview.overall.maeMw)}
                <span className="unit">MW</span>
              </div>
            </div>
            <div className="metric">
              <div className="label">RMSE</div>
              <div className="value">
                {fmtMw(overview.overall.rmseMw)}
                <span className="unit">MW</span>
              </div>
            </div>
            <div className="metric">
              <div className="label">Bias</div>
              <div className="value">
                {fmtMw(overview.overall.biasMw)}
                <span className="unit">MW</span>
              </div>
            </div>
            <div className="metric">
              <div className="label">MAPE</div>
              <div className="value">
                {overview.overall.mapePct ?? "—"}
                <span className="unit">%</span>
              </div>
            </div>
          </div>

          <div className="band-callout">
            <strong>
              Residual band ±{fmtMw(overview.overall.residualBandMw)} MW
            </strong>
            <span>
              {overview.overall.interpretation ??
                "P90 absolute error across decision-window half-hours."}
            </span>
          </div>

          <div className="toolbar">
            <label htmlFor="day">Delivery day</label>
            <select
              id="day"
              value={day}
              onChange={(e) => setDay(e.target.value)}
            >
              {days.map((d) => (
                <option key={d.deliveryDay} value={d.deliveryDay}>
                  {d.deliveryDay}
                  {d.withActual ? "" : " (fc only)"}
                </option>
              ))}
            </select>
          </div>

          <div className="chart-panel">
            <div className="chart-title">
              Decision forecast vs actual · {day} (Europe/London)
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={chartData}>
                <CartesianGrid stroke="rgba(11,28,36,0.08)" />
                <XAxis dataKey="t" tick={{ fontSize: 11 }} minTickGap={40} />
                <YAxis tick={{ fontSize: 11 }} width={56} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  name="Forecast"
                  stroke="#d4a574"
                  strokeWidth={2}
                  strokeDasharray="6 4"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  name="Actual"
                  stroke="#1a6b5c"
                  strokeWidth={2.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section id="accuracy" aria-labelledby="acc-title">
          <p className="section-label">Quantitative accuracy</p>
          <h3 id="acc-title">Where error lives — and how to size cover</h3>
          <p className="lede">
            Absolute error by lead time from gate close, and the signed-error
            shape for {day}. Numbers update with the selected delivery day.
          </p>

          <div className="metric-strip">
            <div className="metric">
              <div className="label">Day MAE</div>
              <div className="value">
                {fmtMw(metrics.overall.maeMw)}
                <span className="unit">MW</span>
              </div>
            </div>
            <div className="metric">
              <div className="label">Day P90 |e|</div>
              <div className="value">
                {fmtMw(metrics.overall.p90AbsErrorMw)}
                <span className="unit">MW</span>
              </div>
            </div>
            <div className="metric">
              <div className="label">Paired HH</div>
              <div className="value">{metrics.overall.n}</div>
            </div>
          </div>

          <div className="chart-panel">
            <div className="chart-title">MAE by lead hours after gate</div>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={metrics.byLeadHour}>
                <CartesianGrid stroke="rgba(11,28,36,0.08)" />
                <XAxis dataKey="leadHours" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} width={48} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="maeMw"
                  name="MAE (MW)"
                  stroke="#1e3a4c"
                  fill="#1a6b5c44"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-panel">
            <div className="chart-title">Signed error distribution (MW)</div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={hist}>
                <CartesianGrid stroke="rgba(11,28,36,0.08)" />
                <XAxis dataKey="mw" tick={{ fontSize: 11 }} minTickGap={24} />
                <YAxis tick={{ fontSize: 11 }} width={40} />
                <Tooltip />
                <Bar dataKey="count" name="Half-hours" fill="#0e3f38" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section id="method" aria-labelledby="method-title">
          <p className="section-label">Methodology</p>
          <h3 id="method-title">What a trader actually had</h3>
          <div className="method-block">
            <p>
              <strong>Decision rule.</strong> For delivery day{" "}
              <code>D</code> (00:00–24:00 Europe/London), take all WINDFOR rows
              with <code>publishTime ≤ 09:20 CET on D−1</code> (EPEX SPOT GB
              day-ahead gate). Keep the latest such publication, then the
              half-hours whose <code>startTime</code> falls on D.
            </p>
            <p>
              <strong>Actuals.</strong> FUELHH stream,{" "}
              <code>fuelType=WIND</code>, national half-hour average MW.
            </p>
            <p>
              <strong>Scope.</strong> January 2026 only. Public Elexon Insights
              stream endpoints — no API key required.
            </p>
            <p>
              <strong>Actionable output.</strong> Residual procurement band =
              P90 absolute forecast error, so thermal / residual cover can be
              sized without pretending the point forecast is exact.
            </p>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>
          Boreas · {overview.dayCount} delivery days ·{" "}
          {overview.pairedHalfHours.toLocaleString("en-GB")} paired half-hours
        </span>
        <span>Built with AI assistance · Elexon BMRS Insights</span>
      </footer>
    </div>
  );
}
