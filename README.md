# Inference Lab

A reproducible vLLM experiment lab for OpenShift that:
- deploys vLLM
- runs batching experiments
- captures latency, RPS, and tokens/sec
- generates charts
- produces an executive-ready HTML report

## What it demonstrates

This lab shows how changing `max_num_batched_tokens` affects:
- average latency
- p95 latency
- requests/sec
- tokens/sec

It is designed to make inference tuning visible and repeatable.

---

## Prerequisites

- Python 3
- `oc` CLI installed and logged into an OpenShift cluster
- Access to a GPU-enabled OpenShift environment
- A Hugging Face token with access to the model

---

## First-time setup

```bash
git clone <your-repo-url>
cd inference-lab
chmod +x bootstrap.sh demo.sh
./bootstrap.sh


## Run Full Demo
source venv/bin/activate
HF_TOKEN=your_actual_hf_token ./demo.sh

open outputs/reports/report.html

## Interactive Experiment Mode

source venv/bin/activate
python3 -m app.run_experiment

##Standard Demo Defaults

The automated demo suite currently uses:

batching values: 1024, 4096, 8192
total requests: 50
concurrency: 15
prompt: Explain 5G network slicing in 2 lines
max tokens: 50

These defaults are defined in:

app/run_batching_suite.py


##Charts
open outputs/reports/tokens_per_sec.png
open outputs/reports/latency.png
open outputs/reports/rps.png



##Final Report
open outputs/reports/report.html

