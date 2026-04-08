import os
import sys
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.buggy_codes import get_challenge_by_id, get_challenges
from data.test_cases import grade


# ─────────────────────────────────────────────
#  TYPED PYDANTIC MODELS  (OpenEnv spec)
# ─────────────────────────────────────────────

class Observation(BaseModel):
    challenge_id:   str   = Field(description="Unique challenge identifier")
    difficulty:     str   = Field(description="easy | medium | hard")
    description:    str   = Field(description="What the agent must fix")
    buggy_code:     str   = Field(description="The broken Python code")
    error_message:  str   = Field(description="Error or wrong-output message")
    hint:           str   = Field(description="Optional hint for the agent")
    step:           int   = Field(description="Current step number")
    max_steps:      int   = Field(description="Max steps allowed per episode")


class Action(BaseModel):
    fixed_code: str = Field(description="Agent's corrected version of the code")


class Reward(BaseModel):
    total:           float = Field(description="Final reward 0.0 - 1.0")
    passed:          bool  = Field(description="Did all tests pass?")
    reason:          str   = Field(description="Human-readable explanation")


class StepResult(BaseModel):
    observation: Observation
    reward:      float
    done:        bool
    info:        Dict[str, Any]


# ─────────────────────────────────────────────
#  CORE ENVIRONMENT
# ─────────────────────────────────────────────

class CodeDebugEnv:
    """
    AI Code Debugging OpenEnv.

    The agent receives a buggy Python snippet + error message,
    returns fixed code, and is scored on whether it runs correctly
    and passes unit tests.

    Multi-agent extensible: each agent gets its own env instance
    but challenges come from the shared challenge pool.
    """

    ENV_NAME = "code-debug-env"
    VERSION  = "1.0.0"

    def __init__(
        self,
        difficulty:  str = "easy",
        max_steps:   int = 5,
        seed:        int = 42,
        task:        str = "easy_001"
    ):
        self.difficulty  = difficulty
        self.max_steps   = max_steps
        self.seed        = seed
        self.task        = task

        self._challenge: Dict[str, Any] = {}
        self._step:      int  = 0
        self._done:      bool = False
        self._rewards:   list = []
        self._best_score: float = 0.0

    # ── OpenEnv API ───────────────────────────

    def reset(self, seed: int = None) -> Observation:
        """Reset env, load a fresh challenge."""
        if seed:
            self.seed = seed
        random.seed(self.seed)

        self._challenge  = get_challenge_by_id(self.task)
        self._step       = 0
        self._done       = False
        self._rewards    = []
        self._best_score = 0.0

        return self._make_observation()

    def step(self, action: Action) -> StepResult:
        """
        Agent submits fixed code.
        Environment grades it and returns reward + next observation.
        """
        if self._done:
            raise RuntimeError("Episode done. Call reset() first.")

        self._step += 1

        # Grade the agent's fix
        grade_result = grade(action.fixed_code, self._challenge)
        score        = float(grade_result.get("score", 0.0))
        passed       = bool(grade_result.get("passed", False))
        reason       = grade_result.get("reason", "")

        # Reward = score (already 0.0-1.0)
        reward = score
        self._rewards.append(reward)
        self._best_score = max(self._best_score, score)

        # Episode ends if passed or max steps reached
        done = passed or self._step >= self.max_steps
        self._done = done

        reward_obj = Reward(total=reward, passed=passed, reason=reason)

        info = {
            "grade_result":  grade_result,
            "reward_detail": reward_obj.model_dump(),
            "best_score":    self._best_score,
            "step":          self._step,
            "challenge_id":  self._challenge["id"],
        }

        return StepResult(
            observation=self._make_observation(),
            reward=reward,
            done=done,
            info=info
        )

    def state(self) -> Dict[str, Any]:
        """Return full current state for checkpointing."""
        return {
            "env_name":     self.ENV_NAME,
            "version":      self.VERSION,
            "task":         self.task,
            "difficulty":   self.difficulty,
            "step":         self._step,
            "max_steps":    self.max_steps,
            "done":         self._done,
            "best_score":   self._best_score,
            "rewards":      list(self._rewards),
            "challenge_id": self._challenge.get("id", ""),
        }

    def close(self):
        """Cleanup — required by OpenEnv spec."""
        self._done = True

    # ── helpers ──────────────────────────────

    def _make_observation(self) -> Observation:
        c = self._challenge
        return Observation(
            challenge_id  = c.get("id", ""),
            difficulty    = c.get("difficulty", self.difficulty),
            description   = c.get("description", ""),
            buggy_code    = c.get("buggy_code", ""),
            error_message = c.get("error_message", ""),
            hint          = c.get("hint", ""),
            step          = self._step,
            max_steps     = self.max_steps
        )


# ─────────────────────────────────────────────
#  SMOKE TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== SMOKE TEST: Easy Task ===")
    env = CodeDebugEnv(difficulty="easy", task="easy_001", max_steps=3)
    obs = env.reset()
    print(f"Challenge : {obs.challenge_id}")
    print(f"Buggy code:\n{obs.buggy_code}")
    print(f"Error     : {obs.error_message}")

    # Correct fix
    fixed = (
        "def add(a, b):\n"
        "    return a + b\n"
        "print(add(3, 4))"
    )
    result = env.step(Action(fixed_code=fixed))
    print(f"\nReward : {result.reward}")
    print(f"Done   : {result.done}")
    print(f"Reason : {result.info['reward_detail']['reason']}")
    print(f"\nState  : {env.state()}")