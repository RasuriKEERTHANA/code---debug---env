from env import CodeDebugEnv, Action
from typing import Dict, Any


# ─────────────────────────────────────────────
#  TASK DEFINITIONS
# ─────────────────────────────────────────────

TASKS = {

    "easy": {
        "name":        "easy",
        "challenge_id": "easy_001",
        "description": (
            "Fix a simple syntax error in a Python function. "
            "The agent must identify and correct a missing colon."
        ),
        "difficulty":  "easy",
        "max_steps":   3,
        "success_threshold": 1.0,
    },

    "medium": {
        "name":        "medium",
        "challenge_id": "medium_001",
        "description": (
            "Fix a logic bug where the code runs but produces wrong output. "
            "The agent must find the semantic error, not just a syntax issue."
        ),
        "difficulty":  "medium",
        "max_steps":   5,
        "success_threshold": 1.0,
    },

    "hard": {
        "name":        "hard",
        "challenge_id": "hard_001",
        "description": (
            "Fix multiple bugs in a BankAccount class. "
            "All 3 unit tests must pass for full score."
        ),
        "difficulty":  "hard",
        "max_steps":   7,
        "success_threshold": 1.0,
    },
}


# ─────────────────────────────────────────────
#  TASK RUNNER + GRADER
# ─────────────────────────────────────────────

def run_task(
    task_name: str,
    agent_fn,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Runs a full episode for a given task using agent_fn.

    agent_fn: callable that takes Observation → returns fixed_code string
    Returns:  dict with score, rewards, steps, success
    """
    if task_name not in TASKS:
        raise ValueError(
            f"Unknown task '{task_name}'. "
            f"Choose from: {list(TASKS.keys())}"
        )

    task = TASKS[task_name]
    env  = CodeDebugEnv(
        difficulty = task["difficulty"],
        max_steps  = task["max_steps"],
        task       = task["challenge_id"],
        seed       = seed
    )

    obs     = env.reset(seed=seed)
    rewards = []
    steps   = 0
    score   = 0.0
    success = False
    done    = False

    while not done and steps < task["max_steps"]:
        # Agent decides what fix to submit
        fixed_code = agent_fn(obs)
        action     = Action(fixed_code=fixed_code)
        result     = env.step(action)

        rewards.append(result.reward)
        steps  += 1
        score   = max(score, result.reward)   # best score across steps
        done    = result.done
        obs     = result.observation

    score   = round(min(max(score, 0.0), 1.0), 4)
    success = score >= task["success_threshold"]

    env.close()

    return {
        "task":       task_name,
        "score":      score,
        "success":    success,
        "steps":      steps,
        "rewards":    rewards,
        "challenge":  task["challenge_id"],
    }


# ─────────────────────────────────────────────
#  GRADERS  (0.0 – 1.0, deterministic)
# ─────────────────────────────────────────────

def grade_task(task_name: str, fixed_code: str) -> Dict[str, Any]:
    """
    Standalone grader — pass a task name and fixed code,
    get back a score. Used by inference.py and validators.
    """
    if task_name not in TASKS:
        raise ValueError(f"Unknown task: {task_name}")

    task = TASKS[task_name]

    def agent_fn(obs):
        return fixed_code

    return run_task(task_name, agent_fn)


# ─────────────────────────────────────────────
#  SMOKE TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("=" * 50)
    print("TASK SMOKE TESTS")
    print("=" * 50)

    # ── Easy ──
    def easy_agent(obs):
        return (
            "def add(a, b):\n"
            "    return a + b\n"
            "print(add(3, 4))"
        )

    result = run_task("easy", easy_agent)
    print(f"\n[EASY]")
    print(f"  Score   : {result['score']}")
    print(f"  Success : {result['success']}")
    print(f"  Steps   : {result['steps']}")
    print(f"  Rewards : {result['rewards']}")

    # ── Medium ──
    def medium_agent(obs):
        return (
            "def find_max(nums):\n"
            "    max_val = nums[0]\n"
            "    for n in nums:\n"
            "        if n > max_val:\n"
            "            max_val = n\n"
            "    return max_val\n"
            "print(find_max([-5, -1, -3]))"
        )

    result = run_task("medium", medium_agent)
    print(f"\n[MEDIUM]")
    print(f"  Score   : {result['score']}")
    print(f"  Success : {result['success']}")
    print(f"  Steps   : {result['steps']}")
    print(f"  Rewards : {result['rewards']}")

    # ── Hard ──
    def hard_agent(obs):
        return (
            "class BankAccount:\n"
            "    def __init__(self, balance):\n"
            "        self.balance = balance\n\n"
            "    def deposit(self, amount):\n"
            "        if amount > 0:\n"
            "            self.balance += amount\n\n"
            "    def withdraw(self, amount):\n"
            "        if amount > self.balance:\n"
            "            return 'Insufficient funds'\n"
            "        self.balance -= amount\n"
            "        return self.balance\n\n"
            "    def get_balance(self):\n"
            "        return self.balance\n\n"
            "acc = BankAccount(100)\n"
            "acc.deposit(50)\n"
            "result = acc.withdraw(200)\n"
            "print(acc.get_balance())"
        )

    result = run_task("hard", hard_agent)
    print(f"\n[HARD]")
    print(f"  Score   : {result['score']}")
    print(f"  Success : {result['success']}")
    print(f"  Steps   : {result['steps']}")
    print(f"  Rewards : {result['rewards']}")

    print("\n" + "=" * 50)
    print("All tasks completed!")