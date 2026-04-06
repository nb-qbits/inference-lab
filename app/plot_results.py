import json
import glob
import re
import matplotlib.pyplot as plt

files = sorted(glob.glob("outputs/runs/batching_*.json"))

batching = []
tokens_sec = []
latency = []
rps = []

for f in files:
    with open(f) as fh:
        data = json.load(fh)

    # skip old/raw files that do not have summary metrics
    if "tokens_per_sec" not in data:
        print(f"Skipping old-format file: {f}")
        continue

    b = int(re.findall(r"\d+", f)[-1])

    batching.append(b)
    tokens_sec.append(data["tokens_per_sec"])
    latency.append(data["avg_latency_sec"])
    rps.append(data["requests_per_sec"])

if not batching:
    raise ValueError("No valid summary files found in outputs/runs/")

combined = sorted(zip(batching, tokens_sec, latency, rps))
batching, tokens_sec, latency, rps = zip(*combined)

plt.figure()
plt.plot(batching, tokens_sec, marker="o")
plt.title("Throughput (tokens/sec) vs Batching")
plt.xlabel("max_num_batched_tokens")
plt.ylabel("tokens/sec")
plt.grid()
plt.savefig("outputs/reports/tokens_per_sec.png")

plt.figure()
plt.plot(batching, latency, marker="o")
plt.title("Latency vs Batching")
plt.xlabel("max_num_batched_tokens")
plt.ylabel("Avg Latency (sec)")
plt.grid()
plt.savefig("outputs/reports/latency.png")

plt.figure()
plt.plot(batching, rps, marker="o")
plt.title("Requests/sec vs Batching")
plt.xlabel("max_num_batched_tokens")
plt.ylabel("RPS")
plt.grid()
plt.savefig("outputs/reports/rps.png")

print("✅ Charts saved in outputs/reports/")
