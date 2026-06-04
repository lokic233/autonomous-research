#!/bin/bash
cd /Users/dengcchi/autonomous-research-v3/experiments/2026-06-04/EXP-0071
source venv/bin/activate
export SSL_CERT_FILE=/opt/facebook/certs/facebook-ca-bundle.cer
export REQUESTS_CA_BUNDLE=/opt/facebook/certs/facebook-ca-bundle.cer
export PIP_CERT=/opt/facebook/certs/facebook-ca-bundle.cer
pip install pillow >> install2.log 2>&1 && echo PILLOW_DONE >> install2.log
pip install torch --index-url https://download.pytorch.org/whl/cpu >> install2.log 2>&1 && echo TORCH_DONE >> install2.log
pip install 'transformers>=4.49' >> install2.log 2>&1 && echo TF_DONE >> install2.log
pip install datasets >> install2.log 2>&1 && echo DATASETS_DONE >> install2.log
echo ALL_DONE >> install2.log
