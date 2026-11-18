import glob
import json
from collections import Counter

files = sorted(glob.glob("data/all.json"))
if not files:
    print("Json file not found at data/all.json")
    raise SystemExit(1)

latest_file = files[-1]
with open(latest_file, "r", encoding="utf-8") as f:
    data = json.load(f)

by_mfr = Counter(item.get("manufacturer", "Unknown") for item in data)

print(f"File: {latest_file}")
print(f"Total Cards: {len(data)}")
print("-" * 28)
for mfr, count in by_mfr.most_common():
    print(f"{mfr:<10}: {count}")
