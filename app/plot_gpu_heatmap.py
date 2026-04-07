import csv
import glob
import re
from pathlib import Path

import matplotlib.pyplot as plt


def load_gpu_files():
    files = sorted(glob.glob("outputs/runs/gpu_*.csv"))
    rows = []

    for f in files:
        batching = int(re.findall(r"\d+", f)[-1])

        with open(f) as fh:
            reader = csv.DictReader(fh)
            vals = []
            for row in reader:
                try:
                    vals.append(float(row["gpu_util"]))
                except Exception:
                    pass

        if vals:
            rows.append((batching, vals))

    return rows


def pad_rows(rows):
    max_len = max(len(v) for _, v in rows)
    padded = []
    labels = []

    for batching, vals in rows:
        if len(vals) < max_len:
            vals = vals + [vals[-1]] * (max_len - len(vals))
        padded.append(vals)
        labels.append(str(batching))

    return padded, labels


def plot_heatmap():
    rows = load_gpu_files()
    if not rows:
        raise ValueError("No GPU CSV files found in outputs/runs/")

    rows = sorted(rows, key=lambda x: x[0])
    data, labels = pad_rows(rows)

    Path("outputs/reports").mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 4))
    plt.imshow(data, aspect="auto")
    plt.colorbar(label="GPU Utilization %")
    plt.yticks(range(len(labels)), labels)
    plt.xlabel("Time (sample index)")
    plt.ylabel("Batching")
    plt.title("GPU Utilization Heatmap")
    plt.tight_layout()
    plt.savefig("outputs/reports/gpu_heatmap.png")
    print("✅ Saved outputs/reports/gpu_heatmap.png")


if __name__ == "__main__":
    plot_heatmap()
