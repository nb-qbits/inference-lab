import json
import time
import statistics
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

NAMESPACE = "inference-lab"
ROUTE_NAME = "lab-vllm"
MODEL = "mistralai/Mistral-7B-Instruct-v0.2"


def get_route_url():
    cmd = [
        "oc", "get", "route", ROUTE_NAME,
        "-n", NAMESPACE,
        "-o", "jsonpath={.spec.host}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    host = result.stdout.strip()

    if not host:
        raise RuntimeError("Could not fetch route host")

    return f"http://{host}/v1/chat/completions"


def one_request(url, prompt, max_tokens):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
    }

    start = time.time()
    try:
        r = requests.post(url, json=payload, timeout=180)
        latency = time.time() - start

        if r.status_code != 200:
            return {"ok": False, "latency": latency, "tokens": 0, "status_code": r.status_code}

        data = r.json()
        tokens = data.get("usage", {}).get("completion_tokens", 0)

        return {"ok": True, "latency": latency, "tokens": tokens, "status_code": r.status_code}

    except Exception:
        return {"ok": False, "latency": 0, "tokens": 0, "status_code": 0}


def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    idx = max(0, min(len(values) - 1, int(len(values) * p) - 1))
    return round(values[idx], 3)


def run_load(total_requests=20, concurrency=5, prompt="Explain 5G network slicing in 2 lines", max_tokens=50):
    url = get_route_url()
    print(f"🌐 Using endpoint: {url}")

    start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(one_request, url, prompt, max_tokens) for _ in range(total_requests)]
        for f in as_completed(futures):
            results.append(f.result())

    end = time.time()

    successes = [r for r in results if r["ok"]]
    latencies = [r["latency"] for r in successes]
    total_tokens = sum(r["tokens"] for r in successes)
    wall_time = end - start

    summary = {
        "total_requests": total_requests,
        "concurrency": concurrency,
        "success_count": len(successes),
        "error_count": total_requests - len(successes),
        "avg_latency_sec": round(statistics.mean(latencies), 3) if latencies else None,
        "p95_latency_sec": percentile(latencies, 0.95),
        "requests_per_sec": round(total_requests / wall_time, 2) if wall_time > 0 else None,
        "tokens_per_sec": round(total_tokens / wall_time, 2) if wall_time > 0 else None,
        "total_tokens": total_tokens,
        "wall_time_sec": round(wall_time, 2),
    }

    print("\n📊 Results:")
    print(json.dumps(summary, indent=2))

    return summary


if __name__ == "__main__":
    run_load()
