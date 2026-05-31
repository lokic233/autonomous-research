#!/bin/bash
# E-B full sweep orchestrator. Runs 3 engines sequentially on GPU 0, collects ROW
# json lines into data/eb_injection_scaling.csv.
set -u
cd /home/dengcchi/committee_naviC
source /tmp/agentenv.sh
export PATH=/home/dengcchi/sglang-env/bin:$PATH
export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
LOG=logs/eb
mkdir -p $LOG data
VLLM=/home/dengcchi/.conda/envs/py312conda/bin/python
SGL=/home/dengcchi/sglang-env/bin/python
HF=/home/dengcchi/sglang-env/bin/python

echo "=== [1/3] vLLM 0.6.6 ===" 
$VLLM eb_runner_vllm.py    > $LOG/vllm_full.log 2>&1
echo "vllm exit $?"
echo "=== [2/3] SGLang 0.5.12 ==="
$SGL eb_runner_sglang.py   > $LOG/sglang_full.log 2>&1
echo "sglang exit $?"
echo "=== [3/3] HF transformers 5.6 ==="
$HF  eb_runner_hf.py       > $LOG/hf_full.log 2>&1
echo "hf exit $?"

echo "=== assembling CSV ==="
python3 - << 'PY'
import json, csv, glob, os
rows=[]
for f in ["logs/eb/vllm_full.log","logs/eb/sglang_full.log","logs/eb/hf_full.log"]:
    if not os.path.exists(f): continue
    for line in open(f):
        if line.startswith("ROW "):
            rows.append(json.loads(line[4:]))
cols=["engine","context_len","inject_pos_pct","ttft_cachehit_ms","ttft_contaminated_ms",
      "penalty_ratio","stddev_hit_ms","stddev_cont_ms","reps","model","pre_tokens","post_tokens","notes"]
with open("data/eb_injection_scaling.csv","w",newline="") as fh:
    w=csv.DictWriter(fh, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow({k:r.get(k,"") for k in cols})
print(f"wrote {len(rows)} rows to data/eb_injection_scaling.csv")
PY
echo "=== DONE ==="
