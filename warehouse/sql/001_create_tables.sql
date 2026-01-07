-- Core SaaS warehouse schema (MVP)

CREATE TABLE IF NOT EXISTS users (
  user_id        UUID PRIMARY KEY,
  email          TEXT UNIQUE,
  created_at     TIMESTAMPTZ NOT NULL,
  country        TEXT,
  signup_source  TEXT
);

CREATE TABLE IF NOT EXISTS subscriptions (
  subscription_id UUID PRIMARY KEY,
  user_id         UUID NOT NULL REFERENCES users(user_id),
  plan            TEXT NOT NULL,                 -- free, basic, pro
  status          TEXT NOT NULL,                 -- active, cancelled
  started_at      TIMESTAMPTZ NOT NULL,
  cancelled_at    TIMESTAMPTZ,
  mrr_usd         NUMERIC(10,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
  event_id     UUID PRIMARY KEY,
  user_id      UUID REFERENCES users(user_id),
  event_name   TEXT NOT NULL,                    -- signup, login, feature_used, payment_failed, etc.
  event_ts     TIMESTAMPTZ NOT NULL,
  properties   JSONB DEFAULT '{}'::jsonb
);

-- Helpful indexes for analytics
CREATE INDEX IF NOT EXISTS idx_events_user_ts ON events(user_id, event_ts);
CREATE INDEX IF NOT EXISTS idx_events_name_ts ON events(event_name, event_ts);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_started ON subscriptions(user_id, started_at);
