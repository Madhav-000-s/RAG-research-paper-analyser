#!/bin/bash
# Run the evaluation harness
cd "$(dirname "$0")/../evaluation"
python eval_runner.py "$@"
