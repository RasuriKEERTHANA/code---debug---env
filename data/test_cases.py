import subprocess
import sys
import tempfile
import os
from typing import Dict, Any


def run_code(code: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Safely runs Python code in a subprocess sandbox.
    Returns stdout, stderr, and success status.
    """
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.py', delete=False, encoding='utf-8'
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success":   result.returncode == 0,
            "stdout":    result.stdout.strip(),
            "stderr":    result.stderr.strip(),
            "timed_out": False
        }
    except subprocess.TimeoutExpired:
        return {
            "success":   False,
            "stdout":    "",
            "stderr":    "TimeoutError: code took too long to run.",
            "timed_out": True
        }
    finally:
        os.unlink(tmp_path)


def grade_easy(fixed_code: str, challenge: Dict[str, Any]) -> Dict[str, Any]:
    """
    Easy grader: just checks if code runs and output matches.
    Score 0.0 - 1.0
    """
    result = run_code(fixed_code)

    if not result["success"]:
        return {
            "score": 0.0,
            "passed": False,
            "reason": f"Code crashed: {result['stderr']}"
        }

    if result["stdout"] == challenge["correct_output"]:
        return {
            "score": 1.0,
            "passed": True,
            "reason": "Output matches expected. All good!"
        }

    # Partial credit — code ran but wrong output
    return {
        "score": 0.3,
        "passed": False,
        "reason": (
            f"Code ran but wrong output. "
            f"Expected: {challenge['correct_output']} | "
            f"Got: {result['stdout']}"
        )
    }


def grade_medium(fixed_code: str, challenge: Dict[str, Any]) -> Dict[str, Any]:
    """
    Medium grader: code must run AND produce correct output.
    Partial credit for running without error.
    Score 0.0 - 1.0
    """
    result = run_code(fixed_code)

    if result["timed_out"]:
        return {
            "score": 0.0,
            "passed": False,
            "reason": "Code timed out — likely infinite loop."
        }

    if not result["success"]:
        return {
            "score": 0.1,
            "passed": False,
            "reason": f"Code still has errors: {result['stderr']}"
        }

    if result["stdout"] == challenge["correct_output"]:
        return {
            "score": 1.0,
            "passed": True,
            "reason": "Correct output. Logic bug fixed!"
        }

    return {
        "score": 0.4,
        "passed": False,
        "reason": (
            f"Runs but wrong output. "
            f"Expected: {challenge['correct_output']} | "
            f"Got: {result['stdout']}"
        )
    }


def grade_hard(fixed_code: str, challenge: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hard grader: runs multiple unit tests against the fixed code.
    Only the class/function definition is kept — demo lines stripped.
    Score 0.0 - 1.0
    """
    unit_tests = _get_unit_tests(challenge["id"])

    if not unit_tests:
        return {
            "score": 0.0,
            "passed": False,
            "reason": f"No unit tests found for {challenge['id']}"
        }

    # Strip demo/print lines — keep only class & function definitions
    clean_lines = []
    skip_keywords = ["acc =", "acc.", "result =", "print(", "print ("]
    for line in fixed_code.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(kw) for kw in skip_keywords):
            continue
        clean_lines.append(line)
    clean_code = "\n".join(clean_lines)

    passed  = 0
    results = []

    for test in unit_tests:
        full_code = clean_code + "\n\n" + test["code"]
        result    = run_code(full_code, timeout=5)

        if result["timed_out"]:
            results.append({
                "test":   test["name"],
                "passed": False,
                "reason": "Timed out"
            })
            continue

        ok = result["success"] and result["stdout"] == test["expected_output"]
        if ok:
            passed += 1
        results.append({
            "test":   test["name"],
            "passed": ok,
            "reason": (
                "OK" if ok else
                f"Expected '{test['expected_output']}' "
                f"got '{result['stdout']}'"
                f" | stderr: {result['stderr']}"
            )
        })

    score = round(passed / len(unit_tests), 2)
    return {
        "score":        score,
        "passed":       score == 1.0,
        "tests_passed": passed,
        "tests_total":  len(unit_tests),
        "test_results": results,
        "reason":       f"{passed}/{len(unit_tests)} unit tests passed."
    }

def _get_unit_tests(challenge_id: str):
    """Unit tests for each hard challenge."""

    tests = {

        "hard_001": [
            {
                "name": "deposit negative amount",
                "code": (
                    "acc = BankAccount(100)\n"
                    "acc.deposit(-50)\n"
                    "print(acc.get_balance())"
                ),
                "expected_output": "100"
            },
            {
                "name": "withdraw insufficient funds",
                "code": (
                    "acc = BankAccount(100)\n"
                    "result = acc.withdraw(200)\n"
                    "print(result)\n"
                    "print(acc.get_balance())"
                ),
                "expected_output": "Insufficient funds\n100"
            },
            {
                "name": "deposit then get balance",
                "code": (
                    "acc = BankAccount(100)\n"
                    "acc.deposit(50)\n"
                    "print(acc.get_balance())"
                ),
                "expected_output": "150"
            },
        ],

        "hard_002": [
            {
                "name": "find middle element",
                "code": (
                    "print(binary_search([1,3,5,7,9], 5))"
                ),
                "expected_output": "2"
            },
            {
                "name": "find first element",
                "code": (
                    "print(binary_search([1,3,5,7,9], 1))"
                ),
                "expected_output": "0"
            },
            {
                "name": "element not in list",
                "code": (
                    "print(binary_search([1,3,5,7,9], 10))"
                ),
                "expected_output": "-1"
            },
        ],

        "hard_003": [
            {
                "name": "deeply nested list",
                "code": (
                    "print(flatten([1, [2, [3, 4]], 5]))"
                ),
                "expected_output": "[1, 2, 3, 4, 5]"
            },
            {
                "name": "empty nested list",
                "code": (
                    "print(flatten([1, [], 2]))"
                ),
                "expected_output": "[1, 2]"
            },
            {
                "name": "already flat list",
                "code": (
                    "print(flatten([1, 2, 3]))"
                ),
                "expected_output": "[1, 2, 3]"
            },
        ],
    }

    return tests.get(challenge_id, [])


def grade(
    fixed_code: str,
    challenge: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main grading entry point.
    Routes to correct grader based on difficulty.
    """
    difficulty = challenge["difficulty"]

    if difficulty == "easy":
        return grade_easy(fixed_code, challenge)
    elif difficulty == "medium":
        return grade_medium(fixed_code, challenge)
    elif difficulty == "hard":
        return grade_hard(fixed_code, challenge)
    else:
        return {
            "score": 0.0,
            "passed": False,
            "reason": f"Unknown difficulty: {difficulty}"
        }