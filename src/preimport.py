"""Pre-import script to set environment variables before any imports."""

import os

# Suppress PyTorch version warnings - must be set before torch is imported
os.environ["TORCH_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
