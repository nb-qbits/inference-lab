#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "❌ HF_TOKEN is not set"
  echo 'Run like: HF_TOKEN=hf_xxx ./demo.sh'
  exit 1
fi

source venv/bin/activate

NAMESPACE="${NAMESPACE:-inference-lab}"
ROUTE_NAME="${ROUTE_NAME:-lab-vllm}"
SERVICE_NAME="${SERVICE_NAME:-lab-vllm}"
POD_NAME="${POD_NAME:-lab-vllm}"

echo "🧹 Cleaning previous outputs..."
mkdir -p outputs/runs outputs/reports
rm -f outputs/runs/batching_*.json
rm -f outputs/reports/*.png outputs/reports/report.html

echo "🧱 Creating namespace if needed..."
oc get ns "${NAMESPACE}" >/dev/null 2>&1 || oc create namespace "${NAMESPACE}"

echo "🔐 Creating/updating Hugging Face secret..."
oc delete secret hf-secret -n "${NAMESPACE}" >/dev/null 2>&1 || true
oc create secret generic hf-secret \
  --from-literal=token="${HF_TOKEN}" \
  -n "${NAMESPACE}"

echo "🧾 Rendering config..."
python3 -m app.render_config

echo "🚢 Deploying vLLM..."
oc delete pod "${POD_NAME}" -n "${NAMESPACE}" >/dev/null 2>&1 || true
oc apply -f outputs/runs/rendered_vllm.yaml

echo "🌐 Creating service + route..."
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Service
metadata:
  name: ${SERVICE_NAME}
  namespace: ${NAMESPACE}
spec:
  selector:
    app: ${SERVICE_NAME}
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: ${ROUTE_NAME}
  namespace: ${NAMESPACE}
spec:
  to:
    kind: Service
    name: ${SERVICE_NAME}
  port:
    targetPort: http
EOF

echo "🧪 Running batching suite..."
python3 -m app.run_batching_suite

echo "📊 Generating charts..."
python3 -m app.plot_results

echo " Generating Heatmap.."
python3 -m app.plot_gpu_heatmap


echo "📝 Generating report..."
python3 -m app.generate_report

REPORT="outputs/reports/report.html"

echo ""
echo "✅ Demo complete"
echo "📄 Report: ${REPORT}"

if command -v open >/dev/null 2>&1; then
  open "${REPORT}"
fi
