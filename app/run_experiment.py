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

PRESETS = [1024, 4096, 8192]


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


def run_one(batching_value, prompt, max_tokens, total_requests, concurrency):
    profile = load_profile()
    profile["max_num_batched_tokens"] = batching_value
    save_profile(profile)

    render_template(TEMPLATE, PROFILE, OUTPUT)
    deploy()
    wait_until_ready()

    summary = run_load(
        total_requests=total_requests,
        concurrency=concurrency,
        prompt=prompt,
        max_tokens=max_tokens,
    )
    summary["max_num_batched_tokens"] = batching_value
    summary["prompt"] = prompt
    summary["max_tokens"] = max_tokens
    save_result(batching_value, summary)


def prompt_next(current_idx):
    print("\nChoose next action:")
    if current_idx + 1 < len(PRESETS):
        print(f"  1. Run next preset ({PRESETS[current_idx + 1]})")
    print("  2. Enter custom max_num_batched_tokens")
    print("  3. Repeat current run")
    print("  4. Change load settings")
    print("  5. Change prompt / max_tokens")
    print("  6. Abort")
    return input("Enter choice: ").strip()


def main():
    total_requests = 20
    concurrency = 5
    max_tokens = 50
    prompt = "Explain 5G network slicing in 2 lines"

    current_idx = 0
    current_value = PRESETS[current_idx]

    while True:
        print(f"\n🚀 Running experiment with max_num_batched_tokens={current_value}")
        print(f"   Load: total_requests={total_requests}, concurrency={concurrency}, max_tokens={max_tokens}")
        print(f"   Prompt: {prompt}")

        run_one(
            batching_value=current_value,
            prompt=prompt,
            max_tokens=max_tokens,
            total_requests=total_requests,
            concurrency=concurrency,
        )

        choice = prompt_next(current_idx)

        if choice == "1" and current_idx + 1 < len(PRESETS):
            current_idx += 1
            current_value = PRESETS[current_idx]

        elif choice == "2":
            custom = input("Enter custom max_num_batched_tokens: ").strip()
            try:
                current_value = int(custom)
            except ValueError:
                print("❌ Invalid number. Keeping current value.")

        elif choice == "3":
            pass

        elif choice == "4":
            tr = input(f"Total requests [{total_requests}]: ").strip()
            cc = input(f"Concurrency [{concurrency}]: ").strip()

            if tr:
                total_requests = int(tr)
            if cc:
                concurrency = int(cc)

        elif choice == "5":
            new_prompt = input(f"Prompt [{prompt}]: ").strip()
            new_max_tokens = input(f"Max tokens [{max_tokens}]: ").strip()

            if new_prompt:
                prompt = new_prompt
            if new_max_tokens:
                max_tokens = int(new_max_tokens)

        elif choice == "6":
            print("🛑 Aborting experiment loop.")
            break

        else:
            print("❌ Invalid choice. Aborting.")
            break


if __name__ == "__main__":
    main()
