#!/usr/bin/env python3
"""Send Pi CPU temperature, CPU usage, and a rolling average to ThingSpeak."""

import time
from collections import deque
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psutil

WRITE_API_KEY = "YOUR_WRITE_API_KEY"
UPDATE_URL = "https://api.thingspeak.com/update"
TEMPERATURE_FILE = Path("/sys/class/thermal/thermal_zone0/temp")
AVERAGE_SAMPLES = 20
UPLOAD_DELAY_SECONDS = 20


def read_temperature():
    return float(TEMPERATURE_FILE.read_text().strip()) / 1000.0


def upload(temperature, cpu_usage, average_temperature):
    body = urlencode({
        "api_key": WRITE_API_KEY,
        "field1": f"{temperature:.2f}",
        "field2": f"{cpu_usage:.2f}",
        "field3": f"{average_temperature:.2f}",
    }).encode("utf-8")
    request = Request(UPDATE_URL, data=body, method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
    })
    with urlopen(request, timeout=10) as response:
        entry_id = response.read().decode("utf-8").strip()
    if not entry_id.isdigit() or int(entry_id) <= 0:
        raise ValueError("ThingSpeak rejected the update; check key, fields, and rate limit.")
    return entry_id


def main():
    if not WRITE_API_KEY or WRITE_API_KEY == "YOUR_WRITE_API_KEY":
        raise SystemExit("Set WRITE_API_KEY to your channel's Write API Key first.")
    temperatures = deque(maxlen=AVERAGE_SAMPLES)
    print("Uploading to ThingSpeak. Press Ctrl+C to stop.", flush=True)
    try:
        while True:
            try:
                # Overall CPU utilization, averaged across all cores over one second.
                cpu_usage = psutil.cpu_percent(interval=1)
                temperature = read_temperature()
                temperatures.append(temperature)
                average_temperature = sum(temperatures) / len(temperatures)
                print(
                    f"Temperature: {temperature:.2f} C | CPU: {cpu_usage:.1f}% | "
                    f"Average ({len(temperatures)} samples): {average_temperature:.2f} C",
                    flush=True,
                )
                entry_id = upload(temperature, cpu_usage, average_temperature)
                print(f"Upload successful. Entry ID: {entry_id}", flush=True)
            except HTTPError as error:
                print(f"Upload failed: HTTP {error.code} {error.reason}", flush=True)
                print(error.read().decode("utf-8", errors="replace"), flush=True)
            except (URLError, OSError, ValueError) as error:
                print(f"Measurement/upload failed: {error}", flush=True)
            # No immediate retries. Wait at least 20 seconds before another upload.
            time.sleep(UPLOAD_DELAY_SECONDS)
    except KeyboardInterrupt:
        print("\nMonitor stopped.", flush=True)


if __name__ == "__main__":
    main()
