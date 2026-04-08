import subprocess
import sys
import threading
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from env import CodeDebugEnv  # your env

app = FastAPI(title="Code Debug OpenEnv")

# ---------- GLOBAL ENV ----------
env = CodeDebugEnv(difficulty="easy", task="easy_001")

# ---------- STORE ----------
results_store = {"status": "starting", "results": []}


# ---------- ACTION MODEL ----------
class Action(BaseModel):
    fixed_code: str


# ---------- INFERENCE THREAD ----------
def run_inference():
    try:
        results_store["status"] = "running"
        result = subprocess.run(
            [sys.executable, "inference.py"],
            capture_output=True,
            text=True,
            timeout=1200
        )
        results_store["status"]    = "completed"
        results_store["stdout"]    = result.stdout
        results_store["stderr"]    = result.stderr
        results_store["exit_code"] = result.returncode
    except Exception as e:
        results_store["status"] = "error"
        results_store["error"]  = str(e)


# ---------- ROOT ----------
@app.get("/")
def root():
    return JSONResponse({
        "env": "code-debug-env",
        "version": "1.0.0",
        "description": "AI Code Debugging OpenEnv",
        "status": results_store.get("status", "starting"),
        "endpoints": ["/", "/health", "/results", "/reset", "/step", "/state"]
    })


# ---------- HEALTH ----------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- RESET ----------
@app.get("/reset")
def reset():
    global env
    env = CodeDebugEnv(difficulty="easy", task="easy_001")
    obs = env.reset()
    return obs.model_dump()


# ---------- STEP (CRITICAL) ----------
@app.post("/step")
def step(action: Action):
    result = env.step(action)
    return result.model_dump()


# ---------- STATE ----------
@app.get("/state")
def state():
    return env.state().model_dump()


# ---------- RESULTS ----------
@app.get("/results")
def results():
    return results_store


# ---------- MAIN ----------
if __name__ == "__main__":
    thread = threading.Thread(target=run_inference, daemon=True)
    thread.start()
    uvicorn.run(app, host="0.0.0.0", port=7860)
