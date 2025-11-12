"""Leer frecuencia cardiaca (real-time) y descargar históricos del anillo Colmi R02.

Uso:
    # lectura en tiempo real
    python scripts/get_hr.py --address CB:2C:18:A7:4A:00 --mode realtime

    # descargar log de un día
    python scripts/get_hr.py --address CB:2C:18:A7:4A:00 --mode log --target 2025-11-12

    # descargar logs entre fechas y guardar a CSV
    python scripts/get_hr.py --address CB:2C:18:A7:4A:00 --mode log --start 2025-11-01 --end 2025-11-12 --csv hr_logs.csv

Notas:
- Las fechas sin zona horaria se interpretan como UTC.
- El script usa la API `Client` del paquete para conectar y pedir registros.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from colmi_r02_client.client import Client
from colmi_r02_client import real_time, hr as hrmod, date_utils


async def realtime_hr(address: str) -> None:
    async with Client(address) as client:
        print("Starting real-time heart rate reading...")
        readings = await client.get_realtime_reading(real_time.RealTimeReading.HEART_RATE)
        if not readings:
            print("No readings obtained (error or ring not worn).")
            return
        valid = [r for r in readings if r != 0]
        print("Raw readings:", readings)
        if not valid:
            print("No non-zero readings returned.")
            return
        print(f"N={len(valid)}  mean={statistics.mean(valid):.1f}  median={statistics.median(valid)}  min={min(valid)}  max={max(valid)}")


async def fetch_hr_for_date(client: Client, target: datetime) -> hrmod.HeartRateLog | hrmod.NoData:
    # client.get_heart_rate_log expects target at start of day (UTC-aware)
    return await client.get_heart_rate_log(target)


def normalize_date_input(dt_str: str | None) -> datetime | None:
    if dt_str is None:
        return None
    # accept YYYY-MM-DD or full ISO
    # let datetime.fromisoformat handle it, fallback to date parse
    try:
        dt = datetime.fromisoformat(dt_str)
    except Exception:
        # try YYYY-MM-DD
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
    if dt.tzinfo is None:
        dt = date_utils.naive_to_aware(dt)
    return date_utils.start_of_day(dt)


async def download_hr_logs(address: str, start: datetime | None, end: datetime | None, csv_path: Path | None) -> None:
    # default to today if not specified
    if start is None and end is None:
        start = date_utils.start_of_day(date_utils.now())
        end = start
    elif start is None:
        start = end
    elif end is None:
        end = start

    # ensure both are aware and start <= end
    if start.tzinfo is None:
        start = date_utils.naive_to_aware(start)
    if end.tzinfo is None:
        end = date_utils.naive_to_aware(end)

    if start > end:
        raise ValueError("start must be <= end")

    rows = []  # (timestamp_iso, hr)

    async with Client(address) as client:
        for d in date_utils.dates_between(start, end):
            print(f"Requesting heart rate log for {d.date().isoformat()}...")
            try:
                log = await fetch_hr_for_date(client, date_utils.start_of_day(d))
            except Exception as e:
                print(f"  Error fetching for {d.date().isoformat()}: {e}")
                continue

            if isinstance(log, hrmod.NoData):
                print("  No data for this date")
                continue

            print(f"  Received {len(log.heart_rates)} samples (range={log.range}, timestamp={log.timestamp.isoformat()})")
            for reading, ts in log.heart_rates_with_times():
                # include zeros but you may filter later
                rows.append((ts.isoformat(), int(reading)))

    if csv_path is not None:
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "heart_rate"])
            for r in rows:
                writer.writerow(r)
        print(f"Written {len(rows)} rows to {csv_path}")
    else:
        # pretty print a short summary
        print(f"Total samples collected: {len(rows)}")
        if len(rows) > 0:
            values = [v for _, v in rows if v != 0]
            if values:
                print(f"Summary (non-zero): N={len(values)} mean={statistics.mean(values):.1f} median={statistics.median(values)} min={min(values)} max={max(values)}")
            else:
                print("All values are zero (no valid heart rate samples)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Colmi R02 HR reader: real-time + historical logs")
    parser.add_argument("--address", required=True, help="MAC address of the ring")
    parser.add_argument("--mode", choices=["realtime", "log"], default="realtime", help="Operation mode")
    parser.add_argument("--target", help="Target date for log (YYYY-MM-DD or ISO). If omitted uses today")
    parser.add_argument("--start", help="Start date for logs (YYYY-MM-DD or ISO)")
    parser.add_argument("--end", help="End date for logs (YYYY-MM-DD or ISO)")
    parser.add_argument("--csv", help="If provided, write logs to this CSV file")

    args = parser.parse_args()

    if args.mode == "realtime":
        asyncio.run(realtime_hr(args.address))
    else:
        target = normalize_date_input(args.target)
        start = normalize_date_input(args.start)
        end = normalize_date_input(args.end)
        # If target provided, override start/end
        if target is not None and args.start is None and args.end is None:
            start = target
            end = target
        csv_path = Path(args.csv) if args.csv else None
        asyncio.run(download_hr_logs(args.address, start, end, csv_path))


if __name__ == "__main__":
    main()
