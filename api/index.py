# api/index.py
# Vercel serverless entry point for the Behind The Headline (BTH) Flask app.
# Vercel calls this module and expects a WSGI-compatible `app` (or `handler`) at module level.

import os
import sys

# ---------------------------------------------------------------------------
# Path setup – make sure the project root (where server.py lives) is in the
# import search path, regardless of the directory Vercel resolves this file from.
# ---------------------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------------------------------------------------------
# Load .env locally (no-op on Vercel since env-vars come from the dashboard).
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
except ImportError:
    pass  # python-dotenv not installed; rely on system / Vercel env vars

# ---------------------------------------------------------------------------
# Import the Flask app defined in server.py
# ---------------------------------------------------------------------------
from server import app  # noqa: E402  (import after sys.path mutation)

# Vercel Python runtime looks for a module-level variable named `app` that is
# a valid WSGI callable.  Flask's `app` already satisfies this requirement.
# No additional wrapping is needed.

