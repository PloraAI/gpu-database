import glob
import json
import sys
from pathlib import Path

if len(sys.argv) > 1:
    source_path = Path(sys.argv[1])
else:
    candidates = sorted(glob.glob("data/all.json"))
    if candidates:
        source_path = Path(candidates[-1])
    elif Path("gpus-merged-full.json").exists():
        source_path = Path("gpus-merged-full.json")
    else:
        raise FileNotFoundError("The source GPU JSON file was not found in the folder.")

with source_path.open("r", encoding="utf-8") as f:
    all_gpus = json.load(f)

buckets = {
    "data/nvidia.json": [],
    "data/amd.json": [],
    "data/intel.json": [],
    "data/other.json": [],
}

for gpu in all_gpus:
    mfr = (gpu.get("manufacturer") or "").strip().upper()
    if mfr == "NVIDIA":
        buckets["data/nvidia.json"].append(gpu)
    elif mfr in {"AMD", "ATI"}:
        buckets["data/amd.json"].append(gpu)
    elif mfr == "INTEL":
        buckets["data/intel.json"].append(gpu)
    else:
        buckets["data/other.json"].append(gpu)

print(f"Source: {source_path} ({len(all_gpus)} card)")
print("-" * 36)
for filename, items in buckets.items():
    with Path(filename).open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"{filename:<15}: {len(items)} kart")