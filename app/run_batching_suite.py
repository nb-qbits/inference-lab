import json
import time
import yaml
import subprocess
from pathlib import Path

from app.render_config import render_template
from app.load_test import run_load

TEMPLATE = "templates/vllm_pod_template.yaml"
PROFILE = "profiles/profile_default.yaml"
OUTPUT = "outputs/runs/rendered_vllm.yaml"

NAMESPACE = "inference-lab"
POD_NAME = "lab-vllm"

BATCH_VALUES = [1024, 4096, 8192]

TOTAL_REQUESTS = 50
CONCURRENCY = 15
PROMPT = "Explain 5G network slicing in 2 lines"
MAX_TOKENS = 50


def load_profile():
    with open(PROFILE) as f:
        return yaml.safe_load(f)


def save_profile(data):
    with open(PROFILE, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def deploy():
    subprocess.run(
        ["oc", "delete", "pod", POD_NAME, "-n", NAMESPACE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(["oc", "apply", "-f", OUTPUT], check=True)


def wait_until_ready():
    print("⏳ Waiting for vLLM endpoint to be ready...")
    host = subprocess.run(
        ["oc", "get", "route", "lab-vllm", "-n", NAMESPACE, "-o", "jsonpath={.spec.host}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    url = f"http://{host}/health"

    while True:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() == "200":
            print("✅ vLLM endpoint is ready")
            break
        time.sleep(5)


def save_result(batching_value, summary):
    Path("outputs/runs").mkdir(parents=True, exist_ok=True)
    out = Path(f"outputs/runs/batching_{batching_value}.json")
    out.write_text(json.dumps(summary, indent=2))
    print(f"💾 Saved {out}")


def run_one(batching_value):
    print(f"\n🚀 Running batching experiment: {batching_value}")

    profile = load_profile()
    profile["max_num_batched_tokens"] = batching_value
    save_profile(profile)

    render_template(TEMPLATE, PROFILE, OUTPUT)
    deploy()
    wait_until_ready()

    summary = run_load(
        total_requests=TOTAL_REQUESTS,
        concurrency=CONCURRENCY,
        prompt=PROMPT,
        max_tokens=MAX_TOKENS,
    )
    summary["max_num_batched_tokens"] = batching_value
    summary["prompt"] = PROMPT
    summary["max_tokens"] = MAX_TOKENS
    summary["total_requests"] = TOTAL_REQUESTS
    summary["concurrency"] = CONCURRENCY

    save_result(batching_value, summary)


if __name__ == "__main__":
    for value in BATCH_VALUES:
        run_one(value)
