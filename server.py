from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import threading

from env import CodeDebugEnv
from tasks import Action

app = FastAPI()

# Global environment + results store
env = CodeDebugEnv(difficulty="easy", task="easy_001")

results_store = {
    "status": "running",
    "stdout": "",
    "stderr": "",
    "exit_code": None
}

# ---------------- BACKGROUND INFERENCE ----------------
def run_inference():
    global results_store
    try:
        result = env.run_inference()

        results_store["status"] = "completed"
        results_store["stdout"] = result.stdout
        results_store["stderr"] = result.stderr
        results_store["exit_code"] = result.returncode

    except Exception as e:
        results_store["status"] = "error"
        results_store["error"] = str(e)


# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {
        "env": "code-debug-env",
        "version": "1.0.0",
        "description": "AI Code Debugging OpenEnv",
        "status": results_store.get("status", "running"),
        "endpoints": ["/", "/health", "/results", "/reset", "/step", "/state"]
    }


# ---------------- HEALTH ----------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------- RESET (CRITICAL FIXED) ----------------
@app.post("/reset")
async def reset(request: Request):
    global env

    # Reinitialize environment (NO max_steps)
    env = CodeDebugEnv(difficulty="easy", task="easy_001")

    obs = env.reset()

    # IMPORTANT: return raw JSON (not wrapped)
    return JSONResponse(content=obs.model_dump())


# ---------------- STEP ----------------


@app.post("/step")
async def step(action: dict):
    try:
        # Convert dict → object with attribute
        class ActionObj:
            def __init__(self, fixed_code):
                self.fixed_code = fixed_code

        action_obj = ActionObj(action.get("fixed_code"))

        result = env.step(action_obj)

        return JSONResponse(content=result.model_dump())

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
# ---------------- STATE ----------------
@app.get("/state")
def state():
    return JSONResponse(content=env.state().model_dump())


# ---------------- RESULTS ----------------
@app.get("/results")
def results():
    return results_store


# ---------------- MAIN ----------------
if __name__ == "__main__":
    thread = threading.Thread(target=run_inference, daemon=True)
    thread.start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
