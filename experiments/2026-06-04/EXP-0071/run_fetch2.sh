#!/bin/bash
cd /Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0071
source venv/bin/activate
export SSL_CERT_FILE=/opt/facebook/certs/facebook-ca-bundle.cer
export REQUESTS_CA_BUNDLE=/opt/facebook/certs/facebook-ca-bundle.cer
export CURL_CA_BUNDLE=/opt/facebook/certs/facebook-ca-bundle.cer
export HF_HUB_DOWNLOAD_TIMEOUT=60
export no_proxy="127.0.0.1,localhost,.facebook.com,.facebook.net,.internalfb.com"
export NO_PROXY="$no_proxy"
NIMG=320 python fetch2.py
