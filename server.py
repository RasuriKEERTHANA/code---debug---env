import subprocess
import sys
import threading
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Code Debug OpenEnv")

results_store = {"status": "starting", "results": []}


def run_inference():
    try:
        results_store["status"] = "running"
        result = subprocess.run(
            [sys.executable, "inference.py"],
            capture_output=True,
            text=True,
            timeout=1200
        )
        results_store["status"]   = "completed"
        results_store["stdout"]   = result.stdout
        results_store["stderr"]   = result.stderr
        results_store["exit_code"] = result.returncode
    except Exception as e:
        results_store["status"] = "error"
        results_store["error"]  = str(e)


@app.get("/")
def root():
    return JSONResponse({
        "env":         "code-debug-env",
        "version":     "1.0.0",
        "description": "AI Code Debugging OpenEnv",
        "status":      results_store.get("status", "starting"),
        "endpoints":   ["/", "/health", "/results", "/reset"]
    })


@app.get("/health")
def health():
    return JSONResponse({"status": "ok", "env": "code-debug-env"})


@app.get("/reset")
def reset():
    from env import CodeDebugEnv
    env = CodeDebugEnv(difficulty="easy", task="easy_001", max_steps=3)
    obs = env.reset()
    return JSONResponse({
        "status":      "ok",
        "observation": obs.model_dump()
    })


@app.get("/results")
def results():
    return JSONResponse(results_store)


if __name__ == "__main__":
    thread = threading.Thread(target=run_inference, daemon=True)
    thread.start()
    uvicorn.run(app, host="0.0.0.0", port=7860)