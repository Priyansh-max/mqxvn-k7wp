const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export type MetricsSummary = {
  n: number;
  maeMw: number | null;
  rmseMw: number | null;
  mapePct: number | null;
  biasMw: number | null;
  p10AbsErrorMw: number | null;
  p50AbsErrorMw: number | null;
  p90AbsErrorMw: number | null;
  residualBandMw: number | null;
  interpretation?: string;
  note?: string;
};

export type SeriesPoint = {
  deliveryDay: string;
  startTime: string;
  publishTime: string | null;
  gateCloseUtc: string;
  forecastMw: number;
  actualMw: number | null;
  errorMw: number | null;
  leadHours: number;
  hourLocal: number;
};

export type Overview = {
  product: string;
  tagline: string;
  deliveryMonth: string;
  overall: MetricsSummary;
  latestDeliveryDay: string | null;
  latestDayMetrics: MetricsSummary | null;
  dayCount: number;
  pairedHalfHours: number;
};

export type MetricsPayload = {
  overall: MetricsSummary;
  byLeadHour: { leadHours: number; n: number; maeMw: number; p90Mw: number }[];
  byHourLocal: { hourLocal: number; n: number; maeMw: number; p90Mw: number }[];
  errorHistogram: { binCentersMw: number[]; counts: number[] };
  deliveryDays: string[];
};

export type DayList = {
  days: {
    deliveryDay: string;
    publishTime: string | null;
    gateCloseUtc: string;
    points: number;
    withActual: number;
  }[];
};

export const api = {
  overview: () => get<Overview>("/api/overview"),
  metrics: (day?: string) =>
    get<MetricsPayload>(day ? `/api/metrics?day=${day}` : "/api/metrics"),
  series: (day?: string) =>
    get<{ points: SeriesPoint[] }>(
      day ? `/api/series?day=${day}` : "/api/series",
    ),
  days: () => get<DayList>("/api/days"),
  methodology: () => get<Record<string, unknown>>("/api/methodology"),
  health: () => get<Record<string, unknown>>("/api/health"),
};
