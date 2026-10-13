#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    /usr/bin/python3 -m venv .venv
    source .venv/bin/activate
    pip install flask pillow
fi

python run.py
