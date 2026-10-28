"""Hermes: polls the storage service for new events, updates the statistics,
and writes them to Redis so Pythia can serve them."""

import json
import logging
import logging.config
import os
import signal
import threading
import time

import redis
import requests
import yaml

LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "log_conf.yml")

with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)

logging.config.dictConfig(log_config)
logger = logging.getLogger("hermes")

# Configuration comes from the environment (set in docker-compose.yml)
STORAGE_URL = os.getenv("STORAGE_URL", "http://localhost:8090")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL_SECONDS", "5"))

STATS_KEY = "statistics"
HTTP_TIMEOUT = 5  # seconds

# A fresh start: nothing counted, no min/max yet, and no cursor (None = ask storage for everything)
DEFAULT_STATS = {
    "num_distance_events": 0,
    "num_steps_events": 0,
    "min_distance": None,
    "max_distance": None,
    "min_steps": None,
    "max_steps": None,
    "last_updated_distance": None,
    "last_updated_steps": None,
}


def load_stats(client):
    raw = client.get(STATS_KEY)
    if raw is None:
        return dict(DEFAULT_STATS)
    # Defaults first, so a key missing from an older saved value still exists
    return {**DEFAULT_STATS, **json.loads(raw)}


def save_stats(client, stats):
    client.set(STATS_KEY, json.dumps(stats))


def fetch_events(http, path, after):
    """Ask storage for the events recorded after `after` (None = all of them)."""
    params = {"after": after} if after else None
    response = http.get(f"{STORAGE_URL}{path}", params=params, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    return response.json()


def merge_extremes(current_min, current_max, values):
    """Fold a batch of values into the stored min and max (either may be None)."""
    if not values:
        return current_min, current_max
    batch_min, batch_max = min(values), max(values)
    new_min = batch_min if current_min is None else min(current_min, batch_min)
    new_max = batch_max if current_max is None else max(current_max, batch_max)
    return new_min, new_max


def apply_events(stats, events, count_key, value_field, min_key, max_key, cursor_key):
    """Update the statistics for ONE event type. Called once per type."""
    if not events:
        return
    stats[count_key] += len(events)
    stats[min_key], stats[max_key] = merge_extremes(
        stats[min_key], stats[max_key], [e[value_field] for e in events]
    )
    # Storage returns events oldest-first, so the last one is the newest.
    # Keep storage's own string: it is exactly what storage accepts back in `after`.
    stats[cursor_key] = events[-1]["recorded_timestamp"]


def run_round(http, client):
    started = time.perf_counter()
    logger.info("Starting a processing round")

    stats = load_stats(client)

    try:
        distance_events = fetch_events(http, "/events/distance", stats["last_updated_distance"])
        steps_events = fetch_events(http, "/events/steps", stats["last_updated_steps"])
    except requests.RequestException as e:
        # Nothing has been saved, so the cursors are unchanged and the next round retries
        logger.error("Storage service unreachable or request failed: %s", e)
        return

    logger.info(
        "Received %d distance and %d steps events from storage",
        len(distance_events), len(steps_events),
    )

    if not distance_events and not steps_events:
        logger.info("No new events; statistics unchanged")
        return

    apply_events(stats, distance_events, "num_distance_events", "distance",
                 "min_distance", "max_distance", "last_updated_distance")
    apply_events(stats, steps_events, "num_steps_events", "steps",
                 "min_steps", "max_steps", "last_updated_steps")

    save_stats(client, stats)

    elapsed = time.perf_counter() - started
    logger.info("Statistics updated in %.3f s: %s", elapsed, stats)


def main():
    stop = threading.Event()
    # `docker compose stop` sends SIGTERM: finish the current wait and exit cleanly
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Hermes started: storage=%s redis=%s interval=%ss",
                STORAGE_URL, REDIS_URL, POLL_INTERVAL)

    with requests.Session() as http:
        while not stop.is_set():
            try:
                run_round(http, client)
            except redis.RedisError as e:
                logger.error("Redis error, will retry next round: %s", e)
            except Exception:
                # A worker must survive a bad round
                logger.exception("Unexpected error during a processing round")
            stop.wait(POLL_INTERVAL)

    client.close()
    logger.info("Hermes stopped")


if __name__ == "__main__":
    main()