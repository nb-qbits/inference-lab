import json
import glob
import re
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_HTML = "outputs/reports/report.html"
RUNS_DIR = "outputs/runs"


def get_env_details():
    try:
        route = subprocess.run(
            ["oc", "get", "route", "lab-vllm", "-n", "inference-lab", "-o", "jsonpath={.spec.host}"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        route = "unknown"

    return {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "inference_engine": "vLLM",
        "namespace": "inference-lab",
        "route": route,
    }


def load_results():
    files = sorted(glob.glob(f"{RUNS_DIR}/batching_*.json"))
    results = []

    for f in files:
        with open(f) as fh:
            d = json.load(fh)

        if "tokens_per_sec" not in d:
            continue

        batching = d.get("max_num_batched_tokens")
        if batching is None:
            matches = re.findall(r"\d+", f)
            batching = int(matches[-1]) if matches else "unknown"

        d["batching"] = batching
        results.append(d)

    return sorted(results, key=lambda x: x["batching"])


def percent_change(old, new):
    if old in (0, None) or new is None:
        return "n/a"
    return f"{((new - old) / old) * 100:.1f}%"


def build_summary(data):
    if not data:
        return "<p>No valid data found.</p>"

    best_throughput = max(data, key=lambda x: x["tokens_per_sec"])
    best_latency = min(data, key=lambda x: x["avg_latency_sec"])
    best_rps = max(data, key=lambda x: x["requests_per_sec"])

    baseline = data[0]
    latest = data[-1]

    return f"""
    <ul>
        <li><b>Best throughput:</b> batching={best_throughput['batching']} delivered {best_throughput['tokens_per_sec']} tokens/sec.</li>
        <li><b>Best latency:</b> batching={best_latency['batching']} delivered {best_latency['avg_latency_sec']} sec average latency.</li>
        <li><b>Best request capacity:</b> batching={best_rps['batching']} delivered {best_rps['requests_per_sec']} requests/sec.</li>
        <li><b>Observed change from first to last run:</b> RPS changed by {percent_change(baseline['requests_per_sec'], latest['requests_per_sec'])}, tokens/sec changed by {percent_change(baseline['tokens_per_sec'], latest['tokens_per_sec'])}, and average latency changed by {percent_change(baseline['avg_latency_sec'], latest['avg_latency_sec'])}.</li>
        <li><b>Executive takeaway:</b> batching should be chosen based on workload intent. Lower values favor responsiveness, while higher values favor system efficiency under concurrent load.</li>
    </ul>
    """


def build_table(data):
    rows = ""
    for d in data:
        rows += f"""
        <tr>
            <td>{d.get('batching', 'n/a')}</td>
            <td>{d.get('total_requests', 'n/a')}</td>
            <td>{d.get('concurrency', 'n/a')}</td>
            <td>{d.get('max_tokens', 'n/a')}</td>
            <td>{d.get('avg_latency_sec', 'n/a')}</td>
            <td>{d.get('p95_latency_sec', 'n/a')}</td>
            <td>{d.get('requests_per_sec', 'n/a')}</td>
            <td>{d.get('tokens_per_sec', 'n/a')}</td>
        </tr>
        """
    return rows


def build_experiment_details(data):
    if not data:
        return "<p>No experiment metadata found.</p>"

    sample = data[0]
    prompt = sample.get("prompt", "n/a")

    return f"""
    <ul>
        <li><b>Prompt:</b> {prompt}</li>
        <li><b>Max tokens:</b> {sample.get('max_tokens', 'n/a')}</li>
        <li><b>Total requests:</b> {sample.get('total_requests', 'n/a')}</li>
        <li><b>Concurrency:</b> {sample.get('concurrency', 'n/a')}</li>
        <li><b>Batching values tested:</b> {", ".join(str(d['batching']) for d in data)}</li>
    </ul>
    """


def generate_html(env, data):
    summary = build_summary(data)
    table_rows = build_table(data)
    experiment_details = build_experiment_details(data)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <html>
    <head>
        <title>vLLM Experiment Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }}
            h1, h2 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f4f4f4; }}
            .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
            img {{ border: 1px solid #ddd; border-radius: 6px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>

    <h1>🚀 vLLM Inference Experiment Report</h1>
    <p><b>Generated:</b> {now}</p>

    <div class="card">
        <h2>🔧 Environment</h2>
        <ul>
            <li><b>Model:</b> {env['model']}</li>
            <li><b>Inference Engine:</b> {env['inference_engine']}</li>
            <li><b>Namespace:</b> {env['namespace']}</li>
            <li><b>Route:</b> {env['route']}</li>
        </ul>
    </div>

    <div class="card">
        <h2>🧪 Experiment Setup</h2>
        {experiment_details}
    </div>

    <div class="card">
        <h2>📊 Results Table</h2>
        <table>
            <tr>
                <th>Batching</th>
                <th>Total Requests</th>
                <th>Concurrency</th>
                <th>Max Tokens</th>
                <th>Avg Latency (s)</th>
                <th>P95 Latency (s)</th>
                <th>RPS</th>
                <th>Tokens/sec</th>
            </tr>
            {table_rows}
        </table>
    </div>

    <div class="card">
        <h2>📈 Charts</h2>
        <img src="gpu_heatmap.png" width="700"><br>
        <img src="tokens_per_sec.png" width="700"><br>
        <img src="latency.png" width="700"><br>
        <img src="rps.png" width="700"><br>
    </div>

    <div class="card">
        <h2>🧠 Executive Summary</h2>
        {summary}
    </div>

    </body>
    </html>
    """

    Path(OUTPUT_HTML).write_text(html)
    print(f"✅ Report generated: {OUTPUT_HTML}")


if __name__ == "__main__":
    Path("outputs/reports").mkdir(parents=True, exist_ok=True)
    env = get_env_details()
    data = load_results()
    generate_html(env, data)
