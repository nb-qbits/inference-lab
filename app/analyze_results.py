import json, re, glob, time

def extract_text(resp):
    try:
        j = json.loads(resp)
        return j["choices"][0]["message"]["content"]
    except:
        return ""

def estimate_tokens(text):
    # quick proxy (good enough for comparison)
    return max(1, int(len(text.split()) * 1.3))

def analyze():
    files = sorted(glob.glob("outputs/runs/batching_*.json"))
    results = []

    for f in files:
        with open(f) as fh:
            raw = fh.read()

        start = time.time()
        txt = extract_text(raw)
        latency = time.time() - start  # parsing time is tiny; proxy only

        tokens = estimate_tokens(txt)
        results.append((f, latency, tokens))

    print("\nBatching | Tokens | (proxy) Latency")
    for f, lat, tok in results:
        b = re.findall(r"\d+", f)[-1]
        print(f"{b:>8} | {tok:>6} | {lat:.4f}s")

if __name__ == "__main__":
    analyze()
