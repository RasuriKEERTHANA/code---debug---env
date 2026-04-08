import os
import sys
from typing import Dict, Any
from pydantic import BaseModel, Field
import random

# Fix import path
sys.path.append(os.path.abspath("."))

from data.buggy_codes import get_challenge_by_id
from data.test_cases import grade


# ─────────────────────────
# MODELS
# ─────────────────────────

class Observation(BaseModel):
    challenge_id: str
    difficulty: str
    description: str
    buggy_code: str
    error_message: str
    hint: str
    step: int
    max_steps: int


class Action(BaseModel):
    fixed_code: str


class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]


# ─────────────────────────
# ENVIRONMENT
# ─────────────────────────

class CodeDebugEnv:

    def __init__(self, difficulty="easy", seed=42, task="easy_001"):
        self.difficulty = difficulty
        self.seed = seed
        self.task = task

        if difficulty == "hard":
            self.max_steps = 6
        elif difficulty == "medium":
            self.max_steps = 4
        else:
            self.max_steps = 3

        self._challenge = {}
        self._step = 0
        self._done = False
        self._rewards = []
        self._best_score = 0.0

    # ─────────────────────────

    def reset(self):
        random.seed(self.seed)

        self._challenge = get_challenge_by_id(self.task)
        self._step = 0
        self._done = False
        self._rewards = []
        self._best_score = 0.0

        return self._make_observation()

    # ─────────────────────────

    def step(self, action: Action):

        if self._done:
            raise RuntimeError("Episode done. Call reset() first.")

        self._step += 1

        grade_result = grade(action.fixed_code, self._challenge)

        score = float(grade_result.get("score", 0.0))
        passed = bool(grade_result.get("passed", False))

        # Reward shaping
        reward = score

        if score > 0:
            reward += 0.1

        if score > self._best_score:
            reward += 0.1

        if score == 0:
            reward = 0.0

        reward = min(reward, 1.0)

        self._rewards.append(reward)
        self._best_score = max(self._best_score, score)

        # Multi-step enforcement
        if passed and self._step >= 2:
            done = True
        else:
            done = self._step >= self.max_steps

        self._done = done

        return StepResult(
            observation=self._make_observation(),
            reward=reward,
            done=done,
            info={"step": self._step}
        )

    # ─────────────────────────

    def _make_observation(self):
        c = self._challenge
        return Observation(
            challenge_id=c.get("id", ""),
            difficulty=c.get("difficulty", self.difficulty),
            description=c.get("description", ""),
            buggy_code=c.get("buggy_code", ""),
            error_message=c.get("error_message", ""),
            hint=c.get("hint", ""),
            step=self._step,
            max_steps=self.max_steps
        )


# ─────────────────────────
# MAIN TEST (VERY IMPORTANT)
# ─────────────────────────

if __name__ == "__main__":
    print("=== TEST RUN ===")

    env = CodeDebugEnv(difficulty="easy", task="easy_001")
    obs = env.reset()

    print("BUGGY CODE:\n", obs.buggy_code)

    for i in range(3):

        # STEP-WISE IMPROVEMENT
        if i == 0:
            fixed = "def add(a,b): return a"   # partial fix
        else:
            fixed = "def add(a,b): return a+b" # correct fix

        result = env.step(Action(fixed_code=fixed))

        print(f"\nStep {i+1}")
        print("Reward:", result.reward)
        print("Done:", result.done)

        if result.done:
            break