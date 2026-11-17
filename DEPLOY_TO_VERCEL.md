# Deploy ManPro to Vercel (Python/Flask)

## Overview
This guide explains how to deploy the **ManPro** Flask application to **Vercel** using Vercel’s Serverless Functions (Python runtime). Vercel will host the API endpoints as serverless functions and serve any static front‑end assets (if present).

---
## Prerequisites
1. **Vercel account** – sign‑up at https://vercel.com.
2. **Vercel CLI** – installed globally:
   ```bash
   npm i -g vercel   # or yarn global add vercel
   ```
3. **Python 3.10+** installed locally.
4. Project already cleaned of secrets (done) and pushed to GitHub.
5. `requirements.txt` listing all Python dependencies (including `flask` and `python-dotenv`). If missing, create it:
   ```bash
   pip freeze > requirements.txt
   ```
6. Ensure your `.env` file is **not** tracked (already in `.gitignore`).

---
## 1. Prepare a Vercel‑compatible entry point
Vercel expects a **handler function** in the `api/` directory. Create a thin wrapper that forwards requests to the existing Flask app.

```bash
# From the project root
mkdir api
```
Create `api/index.py`:

```python
# api/index.py
import os
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

# Load environment variables (works with .env locally)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import the original Flask app defined in server.py
# Adjust import path if server.py defines `app` at module level
from server import app as flask_app

# Vercel expects a plain WSGI callable named `handler`
def handler(event, context):
    # Vercel passes the request as a Flask-like object via `werkzeug` utilities.
    # The easiest way is to let `DispatcherMiddleware` expose the Flask app at root.
    application = DispatcherMiddleware(Response('Not Found', status=404), {
        '/': flask_app,
    })
    return application
```
> **Tip:** If `server.py` already creates a Flask `app` instance, simply import it. Otherwise expose the existing `app` variable.

---
## 2. Add a `vercel.json` configuration file
This tells Vercel to treat the `api` folder as a Python serverless function and routes all traffic to it.

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb"
      }
    },
    {
      "src": "requirements.txt",
      "use": "@vercel/python",
      "config": { "zeroConfig": true }
    }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "/api/index.py" }
  ]
}
```
Place this file at the repository root.

---
## 3. Configure Environment Variables on Vercel
1. Open your Vercel dashboard → **Project Settings** → **Environment Variables**.
2. Add the variables that your app expects (e.g., `DEEPSEEK_API_KEY`, `NEWSAPI_KEY`, `CURRENTS_API_KEY`, `MEDIASTACK_KEY`, `HTTP_TIMEOUT`).
3. Set the same values you would normally keep in `.env`. Vercel injects them at runtime, so the `.env` file is not required on the platform.

---
## 4. Deploy
From the project root run:
```bash
vercel login               # (once) authenticate with your Vercel account
vercel                     # prompts for project name and linking to GitHub repo
```
Vercel will:
- Install dependencies from `requirements.txt`.
- Build the Python serverless function using `@vercel/python`.
- Deploy and give you a preview URL (e.g., `https://project-name.vercel.app`).
- After confirming the preview works, run `vercel --prod` to promote to production.

---
## 5. (Optional) Use a Dockerfile
If you need more control (custom OS packages, specific Python version, etc.), you can deploy via a Dockerfile.
Create `Dockerfile` at the repo root:
```Dockerfile
# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Vercel overrides, but keep for local testing)
EXPOSE 8000

# Start the Flask app (Vercel will use the CMD as the entrypoint)
CMD ["python", "server.py"]
```
Then add a simple `vercel.json` pointing to Docker:
```json
{
  "version": 2,
  "builds": [{ "src": "Dockerfile", "use": "@vercel/docker" }]
}
```
Deploy the same way with `vercel`.

---
## 6. Verify the Deployment
- Visit the Vercel URL, e.g., `https://your-project.vercel.app/health` (or any endpoint you expose).
- Check the logs in Vercel dashboard → **Functions** → **Logs** for any errors.
- Ensure the API responds correctly.

---
## 7. Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| **`ImportError: No module named 'dotenv'`** | Add `python-dotenv` to `requirements.txt` or install it manually. |
| **Timeout / Cold start** | Keep the Flask app lightweight; avoid heavy initialization at import time. |
| **Static assets not served** | Place static files in a `public/` folder; Vercel serves everything there automatically. |
| **Missing environment variable** | Verify the variable is defined in Vercel dashboard (use the same name as in code). |

---
## 8. TL;DR Command Summary
```bash
# 1. Ensure requirements.txt exists
pip freeze > requirements.txt

# 2. Create API wrapper
mkdir api && cat > api/index.py <<'PY'
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from server import app as flask_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

def handler(event, context):
    application = DispatcherMiddleware(Response('Not Found', status=404), {'/': flask_app})
    return application
PY

# 3. Add vercel.json (as shown above)
# 4. Add env vars on Vercel dashboard
# 5. Deploy
vercel login
vercel
# optional production
vercel --prod
```

---
## 9. References
- Vercel Python Serverless Functions: https://vercel.com/docs/concepts/functions/serverless-functions#python
- Vercel CLI docs: https://vercel.com/docs/cli
- Flask on Vercel example: https://github.com/vercel/python/tree/main/examples/flask

---
**Happy deploying!** If you run into any trouble, feel free to ask for further help.
