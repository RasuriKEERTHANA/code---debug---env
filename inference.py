import os
import textwrap
from typing import List, Optional
from openai import OpenAI

from env import CodeDebugEnv, Action
from tasks import TASKS


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

BENCHMARK    = "code-debug-env"
MAX_STEPS    = 5
TEMPERATURE  = 0.3
MAX_TOKENS   = 1024

# 🔥 FIXED (important)
SUCCESS_SCORE_THRESHOLD = 0.9


SYSTEM_PROMPT = textwrap.dedent("""
You are an expert Python debugger.
You will be given buggy Python code and an error message.
Your job is to return the COMPLETE corrected Python code.

Rules:
- Return ONLY the fixed Python code
- No explanations
- No markdown
- No ``` blocks
- Keep structure same
""").strip()


# ─────────────────────────────────────────────
# LOG FUNCTIONS (REQUIRED FORMAT)
# ─────────────────────────────────────────────

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    error_val = error if error else "null"
    done_val  = str(done).lower()

    action_short = action.replace("\n", "\\n")[:200]

    print(
        f"[STEP] step={step} action={action_short} "
        f"reward={reward:.2f} done={done_val} error={error_val}",
        flush=True
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)

    print(
        f"[END] success={str(success).lower()} "
        f"steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True
    )


# ─────────────────────────────────────────────
# LLM CALL
# ─────────────────────────────────────────────

def get_fixed_code(client: OpenAI, obs, history: List[str]) -> str:

    history_block = "\n".join(history[-3:]) if history else "None"

    prompt = textwrap.dedent(f"""
    Challenge: {obs.description}

    Buggy code:
    {obs.buggy_code}

    Error:
    {obs.error_message}

    Hint:
    {obs.hint}

    Previous attempts:
    {history_block}

    Return ONLY fixed Python code:
    """).strip()

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )

        text = (response.choices[0].message.content or "").strip()

        # Remove ``` if model adds
        if text.startswith("```"):
            text = "\n".join([l for l in text.split("\n") if not l.startswith("```")]).strip()

        return text if text else obs.buggy_code

    except Exception as e:
        print(f"[DEBUG] LLM error: {e}", flush=True)
        return obs.buggy_code


# ─────────────────────────────────────────────
# RUN SINGLE TASK
# ─────────────────────────────────────────────

def run_task(client: OpenAI, task_name: str):

    task_cfg = TASKS[task_name]

    # 🔥 FIXED (removed max_steps)
    env = CodeDebugEnv(
        difficulty=task_cfg["difficulty"],
        task=task_cfg["challenge_id"],
        seed=42
    )

    obs = env.reset()

    rewards = []
    history = []

    steps_taken = 0
    score = 0.0
    success = False
    done = False

    log_start(task_name, BENCHMARK, MODEL_NAME)

    try:
        for step in range(1, MAX_STEPS + 1):

            if done:
                break

            error = None
            fixed_code = get_fixed_code(client, obs, history)

            try:
                result = env.step(Action(fixed_code=fixed_code))
                reward = result.reward
                done   = result.done
                obs    = result.observation

            except Exception as e:
                reward = 0.0
                done   = False
                error  = str(e)[:80]

            rewards.append(reward)
            steps_taken = step
            score = max(score, reward)

            # Debug (optional but useful)
            print(f"[DEBUG] current score={score}", flush=True)

            log_step(step, fixed_code, reward, done, error)

            history.append(f"step={step} reward={reward:.2f}")

        score = round(min(max(score, 0.0), 1.0), 2)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            env.close()   # 🔥 safe now
        except:
            pass

        log_end(success, steps_taken, score, rewards)

    return {
        "task": task_name,
        "score": score,
        "success": success,
        "steps": steps_taken
    }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():

    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY
    )

    results = []

    for task in ["easy", "medium", "hard"]:

        print("\n" + "="*50, flush=True)
        print(f"Running task: {task.upper()}", flush=True)
        print("="*50, flush=True)

        res = run_task(client, task)
        results.append(res)

    print("\n" + "="*50, flush=True)
    print("FINAL SUMMARY", flush=True)
    print("="*50, flush=True)

    for r in results:
        status = "PASS" if r["success"] else "FAIL"
        print(f"[{status}] {r['task']} score={r['score']:.2f} steps={r['steps']}", flush=True)


if __name__ == "__main__":
    main()