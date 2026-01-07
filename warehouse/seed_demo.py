import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple

import psycopg2
import json

RANDOM_SEED = 42

COUNTRIES = ["US", "CA", "IN", "GB", "DE", "AU"]
SOURCES = ["google", "linkedin", "github", "referral", "twitter"]
PLANS = ["free", "basic", "pro"]
PLAN_MRR = {"free": 0.0, "basic": 29.0, "pro": 99.0}

EVENT_NAMES = [
    "signup",
    "login",
    "feature_used",
    "invite_sent",
    "billing_page_viewed",
    "payment_failed",
]

def env(name: str, default: Optional[str] = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return val

def connect():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=env("POSTGRES_DB"),
        user=env("POSTGRES_USER"),
        password=env("POSTGRES_PASSWORD"),
    )

def reset_tables(conn) -> None:
    with conn.cursor() as cur:
        # Truncate all related tables in one command to satisfy FK constraints
        cur.execute("TRUNCATE TABLE events, subscriptions, users RESTART IDENTITY;")
    conn.commit()

def seed_users(conn, n_users: int = 50) -> List[Tuple[uuid.UUID, datetime]]:
    random.seed(RANDOM_SEED)
    now = datetime.now(timezone.utc)
    users: List[Tuple[uuid.UUID, datetime]] = []

    with conn.cursor() as cur:
        for i in range(n_users):
            user_id = uuid.uuid4()
            created_at = now - timedelta(days=random.randint(1, 120), hours=random.randint(0, 23))
            email = f"user{i+1}@demo.local"
            country = random.choice(COUNTRIES)
            source = random.choice(SOURCES)

            cur.execute(
                """
                INSERT INTO users (user_id, email, created_at, country, signup_source)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (str(user_id), email, created_at, country, source),
            )
            users.append((user_id, created_at))

    conn.commit()
    return users

def seed_subscriptions(conn, users: List[Tuple[uuid.UUID, datetime]], n_subscriptions: int = 40):
    random.seed(RANDOM_SEED + 1)
    now = datetime.now(timezone.utc)
    subs = []

    with conn.cursor() as cur:
        sub_users = random.sample(users, k=min(n_subscriptions, len(users)))
        for (user_id, user_created_at) in sub_users:
            subscription_id = uuid.uuid4()
            plan = random.choices(PLANS, weights=[0.45, 0.35, 0.20], k=1)[0]
            started_at = user_created_at + timedelta(days=random.randint(0, 10))

            cancelled = (random.random() < 0.22) and (plan != "free")
            cancelled_at = None
            status = "active"

            if cancelled:
                cancelled_at = started_at + timedelta(days=random.randint(7, 60))
                if cancelled_at > now:
                    cancelled_at = None
                    status = "active"
                else:
                    status = "cancelled"

            mrr = float(PLAN_MRR[plan])

            cur.execute(
                """
                INSERT INTO subscriptions
                (subscription_id, user_id, plan, status, started_at, cancelled_at, mrr_usd)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(subscription_id), str(user_id), plan, status, started_at, cancelled_at, mrr),
            )
            subs.append((subscription_id, user_id, started_at, cancelled_at, plan))

    conn.commit()
    return subs

def seed_events(conn, users, subs, events_per_user_range=(5, 25)) -> None:
    random.seed(RANDOM_SEED + 2)
    now = datetime.now(timezone.utc)

    paid_users = {str(u) for (_, u, _, _, plan) in subs if plan in ("basic", "pro")}

    with conn.cursor() as cur:
        for (user_id, user_created_at) in users:
            n_events = random.randint(events_per_user_range[0], events_per_user_range[1])
            user_id_str = str(user_id)

            for _ in range(n_events):
                event_id = uuid.uuid4()

                if user_id_str in paid_users:
                    name = random.choices(EVENT_NAMES, weights=[1, 6, 7, 3, 2, 1], k=1)[0]
                else:
                    name = random.choices(EVENT_NAMES, weights=[1, 5, 4, 1, 1, 2], k=1)[0]

                start = user_created_at
                delta_seconds = int((now - start).total_seconds())
                if delta_seconds <= 0:
                    event_ts = now
                else:
                    event_ts = start + timedelta(seconds=random.randint(0, delta_seconds))

                props: Dict[str, Any] = {}
                if name == "feature_used":
                    props = {"feature": random.choice(["export_csv", "dashboards", "api_access", "alerts"])}
                elif name == "payment_failed":
                    props = {"reason": random.choice(["card_declined", "insufficient_funds", "expired_card"])}

                cur.execute(
                    """
                    INSERT INTO events (event_id, user_id, event_name, event_ts, properties)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (str(event_id), user_id_str, name, event_ts, json.dumps(props)),
                )

    conn.commit()

def main() -> None:
    conn = connect()
    try:
        reset_tables(conn)
        users = seed_users(conn, n_users=50)
        subs = seed_subscriptions(conn, users, n_subscriptions=40)
        seed_events(conn, users, subs)
        print("Seed complete ✅")
        print(f"Users: {len(users)}")
        print(f"Subscriptions: {len(subs)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
