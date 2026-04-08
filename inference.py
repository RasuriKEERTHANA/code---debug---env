import os
import sys
import textwrap
from typing import List, Optional
from openai import OpenAI

from env import CodeDebugEnv, Action
from tasks import TASKS

# ─────────────────────────────────────────────
#  CONFIG  (from environment variables)
# ─────────────────────────────────────────────

API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK    = "code-debug-env"
MAX_STEPS    = 5
TEMPERATURE  = 0.3
MAX_TOKENS   = 1024
SUCCESS_SCORE_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert Python debugger.
    You will be given buggy Python code and an error message.
    Your job is to return the COMPLETE corrected Python code.

    Rules:
    - Return ONLY the fixed Python code, nothing else.
    - No explanations, no markdown, no code fences.
    - Keep the original structure — only fix the bugs.
    - Make sure the code runs and produces the correct output.
""").strip()


# ─────────────────────────────────────────────
#  STDOUT LOG FUNCTIONS  (exact format required)
# ─────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int,
    action: str,
    reward: float,
    done: bool,
    error: Optional[str]
) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    # Truncate action to avoid overly long lines
    action_short = action.replace("\n", "\\n")[:120]
    print(
        f"[STEP] step={step} action={action_short} "
        f"reward={reward:.2f} done={done_val} error={error_val}",
        flush=True
    )


def log_end(
    success: bool,
    steps: int,
    score: float,
    rewards: List[float]
) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} "
        f"steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True
    )


# ─────────────────────────────────────────────
#  LLM CALL
# ─────────────────────────────────────────────

def get_fixed_code(
    client: OpenAI,
    obs,
    history: List[str]
) -> str:
    """Ask the LLM to fix the buggy code."""

    history_block = "\n".join(history[-3:]) if history else "None"

    user_prompt = textwrap.dedent(f"""
        Challenge: {obs.description}

        Buggy code:
        {obs.buggy_code}

        Error / wrong output:
        {obs.error_message}

        Hint: {obs.hint}

        Previous attempts:
        {history_block}

        Return ONLY the complete fixed Python code:
    """).strip()

    try:
        completion = client.chat.completions.create(
            model       = MODEL_NAME,
            messages    = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature = TEMPERATURE,
            max_tokens  = MAX_TOKENS,
            stream      = False,
        )
        text = (completion.choices[0].message.content or "").strip()
        # Strip markdown fences if model adds them
        if text.startswith("```"):
            lines = text.split("\n")
            text  = "\n".join(
                l for l in lines
                if not l.startswith("```")
            ).strip()
        return text if text else obs.buggy_code

    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return obs.buggy_code


# ─────────────────────────────────────────────
#  SINGLE TASK RUNNER
# ─────────────────────────────────────────────

def run_task(client: OpenAI, task_name: str) -> dict:
    task_cfg = TASKS[task_name]

    env = CodeDebugEnv(
        difficulty = task_cfg["difficulty"],
        max_steps  = MAX_STEPS,
        task       = task_cfg["challenge_id"],
        seed       = 42
    )

    obs          = env.reset()
    rewards: List[float] = []
    steps_taken  = 0
    score        = 0.0
    success      = False
    done         = False
    history: List[str] = []

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            error = None
            fixed_code = get_fixed_code(client, obs, history)

            try:
                action = Action(fixed_code=fixed_code)
                result = env.step(action)
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

            log_step(
                step   = step,
                action = fixed_code,
                reward = reward,
                done   = done,
                error  = error
            )

            history.append(
                f"Step {step}: reward={reward:.2f} passed={done}"
            )

        score   = round(min(max(score, 0.0), 1.0), 2)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)

        log_end(
            success = success,
            steps   = steps_taken,
            score   = score,
            rewards = rewards
        )

    return {
        "task":    task_name,
        "score":   score,
        "success": success,
        "steps":   steps_taken,
        "rewards": rewards
    }


# ─────────────────────────────────────────────
#  MAIN — runs all 3 tasks
# ─────────────────────────────────────────────

def main():
    client = OpenAI(
        base_url = API_BASE_URL,
        api_key  = API_KEY
    )

    all_results = []

    for task_name in ["easy", "medium", "hard"]:
        print(f"\n{'='*50}", flush=True)
        print(f"Running task: {task_name.upper()}", flush=True)
        print(f"{'='*50}", flush=True)

        result = run_task(client, task_name)
        all_results.append(result)

    # Summary
    print(f"\n{'='*50}", flush=True)
    print("FINAL SUMMARY", flush=True)
    print(f"{'='*50}", flush=True)
    for r in all_results:
        status = "PASS" if r["success"] else "FAIL"
        print(
            f"[{status}] {r['task']:8s} "
            f"score={r['score']:.2f} "
            f"steps={r['steps']}",
            flush=True
        )


if __name__ == "__main__":
    main()