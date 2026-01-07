-- Analytics views (MVP)

-- Active subscriptions as-of "now" (based on status field from seeded data)
CREATE OR REPLACE VIEW v_active_subscriptions AS
SELECT
  subscription_id,
  user_id,
  plan,
  started_at,
  cancelled_at,
  mrr_usd
FROM subscriptions
WHERE status = 'active';

-- Daily MRR time series (simple: sum of MRR for subscriptions active on that day)
-- We generate a date series for the last 120 days to keep it small.
CREATE OR REPLACE VIEW v_daily_mrr AS
WITH days AS (
  SELECT generate_series(
    (CURRENT_DATE - INTERVAL '120 days')::date,
    CURRENT_DATE::date,
    INTERVAL '1 day'
  )::date AS day
),
active_on_day AS (
  SELECT
    d.day,
    s.subscription_id,
    s.mrr_usd
  FROM days d
  JOIN subscriptions s
    ON s.started_at::date <= d.day
   AND (s.cancelled_at IS NULL OR s.cancelled_at::date > d.day)
   AND s.plan IN ('basic', 'pro')
)
SELECT
  day,
  ROUND(SUM(mrr_usd)::numeric, 2) AS mrr_usd
FROM active_on_day
GROUP BY day
ORDER BY day;

-- Daily churn count (subscriptions that got cancelled on that day)
CREATE OR REPLACE VIEW v_daily_churn AS
SELECT
  cancelled_at::date AS day,
  COUNT(*) AS churned_subscriptions
FROM subscriptions
WHERE cancelled_at IS NOT NULL
  AND plan IN ('basic', 'pro')
GROUP BY cancelled_at::date
ORDER BY day;

-- Daily Active Users (DAU): distinct users with any event that day
CREATE OR REPLACE VIEW v_dau AS
SELECT
  event_ts::date AS day,
  COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY event_ts::date
ORDER BY day;

-- Weekly Active Users (WAU): distinct users with events in that ISO week
CREATE OR REPLACE VIEW v_wau AS
SELECT
  date_trunc('week', event_ts)::date AS week_start,
  COUNT(DISTINCT user_id) AS wau
FROM events
GROUP BY date_trunc('week', event_ts)::date
ORDER BY week_start;
