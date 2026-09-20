"""Generate small synthetic OHLCV CSV fixtures for demos and manual testing.

Not real market data. Produces a mildly noisy uptrend so the bundled demo
(`python -m trading_agent.main scan`) has something to find. Re-run this
after changing the parameters below to regenerate data/samples/*.csv.
"""
from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def generate_trending_candles(
    count: int, start_price: float, step_minutes: int, drift: float, noise: float, seed: int
):
    random.seed(seed)
    start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = start_price
    candles = []
    for i in range(count):
        time = start_time + timedelta(minutes=step_minutes * i)
        open_price = price
        price += drift + random.uniform(-noise, noise) + 0.15 * noise * math.sin(i / 8)
        close_price = price
        high = max(open_price, close_price) + random.uniform(0, noise)
        low = min(open_price, close_price) - random.uniform(0, noise)
        candles.append((time, open_price, high, low, close_price, random.uniform(100, 1000)))
    return candles


def write_csv(path: Path, candles) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "open", "high", "low", "close", "volume"])
        for time, o, h, l, c, v in candles:
            writer.writerow([time.isoformat(), f"{o:.5f}", f"{h:.5f}", f"{l:.5f}", f"{c:.5f}", f"{v:.1f}"])


def main() -> None:
    h4 = generate_trending_candles(220, start_price=1.0800, step_minutes=240, drift=0.0006, noise=0.0009, seed=1)
    write_csv(OUTPUT_DIR / "EURUSD_H4.csv", h4)

    m15 = generate_trending_candles(
        220, start_price=h4[-1][4], step_minutes=15, drift=0.00012, noise=0.00035, seed=2
    )
    write_csv(OUTPUT_DIR / "EURUSD_M15.csv", m15)

    print(f"Wrote sample data to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
