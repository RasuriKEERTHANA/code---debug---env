from env import CodeDebugEnv, Action
from typing import Dict, Any


# ─────────────────────────────────────────────
# TASK DEFINITIONS
# ─────────────────────────────────────────────

TASKS = {

    "easy": {
        "name": "easy",
        "challenge_id": "easy_001",
        "description": "Fix a simple syntax error in a Python function.",
        "difficulty": "easy",
        "max_steps": 3,
        "success_threshold": 1.0,
    },

    "medium": {
        "name": "medium",
        "challenge_id": "medium_001",   # ✅ FIXED
        "description": "Fix a logic bug in a Python function.",
        "difficulty": "medium",
        "max_steps": 5,
        "success_threshold": 1.0,
    },

    "hard": {
        "name": "hard",
        "challenge_id": "hard_001",   # ✅ FIXED
        "description": "Fix multiple bugs in a class implementation.",
        "difficulty": "hard",
        "max_steps": 7,
        "success_threshold": 1.0,
    },
}


# ─────────────────────────────────────────────
# TASK RUNNER
# ─────────────────────────────────────────────

def run_task(
    task_name: str,
    agent_fn,
    seed: int = 42
) -> Dict[str, Any]:

    if task_name not in TASKS:
        raise ValueError(f"Unknown task '{task_name}'")

    task = TASKS[task_name]

    # Initialize environment
    env = CodeDebugEnv(
        difficulty=task["difficulty"],
        task=task["challenge_id"],
        seed=seed
    )

    obs = env.reset()

    rewards = []
    steps = 0
    score = 0.0
    success = False
    done = False

    # Run episode
    while not done and steps < task["max_steps"]:

        fixed_code = agent_fn(obs)
        action = Action(fixed_code=fixed_code)

        result = env.step(action)

        rewards.append(result.reward)
        steps += 1
        score = max(score, result.reward)
        done = result.done
        obs = result.observation

    score = round(min(max(score, 0.0), 1.0), 4)
    success = score >= task["success_threshold"]

    try:
        env.close()
    except:
        pass

    return {
        "task": task_name,
        "score": score,
        "success": success,
        "steps": steps,
        "rewards": rewards,
        "challenge": task["challenge_id"],
    }


# ─────────────────────────────────────────────
# GRADER WRAPPER
# ─────────────────────────────────────────────

def grade_task(task_name: str, fixed_code: str) -> Dict[str, Any]:

    def agent_fn(_):
        return fixed_code

    return run_task(task_name, agent_fn)


# ─────────────────────────────────────────────
# SMOKE TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("=" * 50)
    print("TASK TESTS")
    print("=" * 50)

    def agent(obs):
        return obs.buggy_code  # dummy

    for task in ["easy", "medium", "hard"]:
        print(f"\n[{task.upper()}]")
        print(run_task(task, agent))

    print("\nAll tests done!")