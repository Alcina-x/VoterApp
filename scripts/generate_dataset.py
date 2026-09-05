from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.main import VOTERS, STATIONS, EVENTS

OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)

def write_csv(name, rows):
    rows = list(rows)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

write_csv("voters.csv", VOTERS)
write_csv("polling_stations.csv", STATIONS)
write_csv("processing_events.csv", EVENTS)
write_csv("anomalies_ground_truth.csv", (v for v in VOTERS if v["anomaly_type"]))
print(f"Generated {len(VOTERS):,} voters, {len(STATIONS)} stations, {len(EVENTS):,} events")
