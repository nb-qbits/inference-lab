import subprocess
import time
from pathlib import Path

NAMESPACE = "inference-lab"
POD_NAME = "lab-vllm"


def start_gpu_capture(tag: str):
    """
    Starts a background GPU sampler and writes CSV to outputs/runs/gpu_<tag>.csv
    """
    Path("outputs/runs").mkdir(parents=True, exist_ok=True)
    out_file = Path(f"outputs/runs/gpu_{tag}.csv")

    cmd = f"""
oc exec -n {NAMESPACE} {POD_NAME} -- bash -lc '
while true; do
  TS=$(date +%s)
  nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | \
  awk -v ts="$TS" -F", " '"'"'{{print ts "," $1 "," $2 "," $3}}'"'"'
  sleep 1
done
'
""".strip()

    f = open(out_file, "w")
    f.write("timestamp,gpu_util,memory_used_mb,memory_total_mb\n")
    f.flush()

    proc = subprocess.Popen(
        ["bash", "-lc", cmd],
        stdout=f,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    return proc, f, str(out_file)


def stop_gpu_capture(proc, file_handle):
    """
    Stops the background sampler cleanly.
    """
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    if file_handle:
        file_handle.close()
