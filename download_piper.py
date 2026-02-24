#!/usr/bin/env python3
from huggingface_hub import hf_hub_download
import os

# Try different paths
paths_to_try = [
    ('en_US-lessac-medium.onnx', 'en_US-lessac-medium.onnx.json'),
    ('en_US/lessac/medium.onnx', 'en_US/lessac/medium.onnx.json'),
    ('en_US-lessac-mediumonnx', 'en_US-lessac-medium.json'),
]

for model, config in paths_to_try:
    try:
        print(f"Trying: {model}")
        m = hf_hub_download('rhasspy/piper-voices', model, local_dir='~/.cache/piper_test')
        c = hf_hub_download('rhasspy/piper-voices', config, local_dir='~/.cache/piper_test')
        print(f'SUCCESS!')
        print(f'Model: {m}')
        print(f'Config: {c}')
        break
    except Exception as e:
        print(f'Failed: {e}')
