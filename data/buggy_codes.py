from typing import List, Dict, Any

def get_challenges() -> List[Dict[str, Any]]:
    """
    Collection of buggy Python challenges.
    Each challenge has:
      - id, difficulty, description
      - buggy_code: the broken code agent must fix
      - error_message: what Python throws
      - correct_output: expected result when fixed
      - hint: optional nudge
    """
    return [

        # ── EASY: Syntax Errors ──────────────────────────────────────

        {
            "id": "easy_001",
            "difficulty": "easy",
            "description": "Fix the function that adds two numbers.",
            "buggy_code": (
                "def add(a, b)\n"
                "    return a + b\n"
                "print(add(3, 4))"
            ),
            "error_message": "SyntaxError: expected ':'",
            "correct_output": "7",
            "hint": "Check the function definition line."
        },
        {
            "id": "easy_002",
            "difficulty": "easy",
            "description": "Fix the loop that prints numbers 1 to 5.",
            "buggy_code": (
                "for i in range(1, 6)\n"
                "    print(i)"
            ),
            "error_message": "SyntaxError: expected ':'",
            "correct_output": "1\n2\n3\n4\n5",
            "hint": "for loops need a colon at the end."
        },
        {
            "id": "easy_003",
            "difficulty": "easy",
            "description": "Fix the function that checks if a number is even.",
            "buggy_code": (
                "def is_even(n):\n"
                "return n % 2 == 0\n"
                "print(is_even(4))"
            ),
            "error_message": "IndentationError: expected an indented block",
            "correct_output": "True",
            "hint": "Check indentation inside the function."
        },

        # ── MEDIUM: Logic Bugs ───────────────────────────────────────

        {
            "id": "medium_001",
            "difficulty": "medium",
            "description": "Fix the function that finds the maximum in a list.",
            "buggy_code": (
                "def find_max(nums):\n"
                "    max_val = 0\n"
                "    for n in nums:\n"
                "        if n > max_val:\n"
                "            max_val = n\n"
                "    return max_val\n"
                "print(find_max([-5, -1, -3]))"
            ),
            "error_message": "No error — but wrong output. Expected: -1, Got: 0",
            "correct_output": "-1",
            "hint": "What happens when all numbers are negative?"
        },
        {
            "id": "medium_002",
            "difficulty": "medium",
            "description": "Fix the factorial function.",
            "buggy_code": (
                "def factorial(n):\n"
                "    result = 0\n"
                "    for i in range(1, n + 1):\n"
                "        result *= i\n"
                "    return result\n"
                "print(factorial(5))"
            ),
            "error_message": "No error — but wrong output. Expected: 120, Got: 0",
            "correct_output": "120",
            "hint": "Check the initial value of result."
        },
        {
            "id": "medium_003",
            "difficulty": "medium",
            "description": "Fix the function that reverses a string.",
            "buggy_code": (
                "def reverse_string(s):\n"
                "    result = ''\n"
                "    for i in range(len(s)):\n"
                "        result += s[i]\n"
                "    return result\n"
                "print(reverse_string('hello'))"
            ),
            "error_message": "No error — but wrong output. Expected: olleh, Got: hello",
            "correct_output": "olleh",
            "hint": "You need to iterate in reverse order."
        },

        # ── HARD: Multiple Bugs + Unit Tests ────────────────────────

        {
            "id": "hard_001",
            "difficulty": "hard",
            "description": (
                "Fix the BankAccount class. "
                "It has 3 bugs. All unit tests must pass."
            ),
            "buggy_code": (
                "class BankAccount:\n"
                "    def __init__(self, balance):\n"
                "        self.balance = balance\n\n"
                "    def deposit(self, amount):\n"
                "        if amount > 0:\n"
                "            self.balance += amount\n\n"
                "    def withdraw(self, amount):\n"
                "        if amount > self.balance:\n"
                "            return 'Insufficient funds'\n"
                "        self.balance -= amount\n\n"
                "    def get_balance(self):\n"
                "        return self.balance\n\n"
                "acc = BankAccount(100)\n"
                "acc.deposit(50)\n"
                "acc.withdraw(200)\n"
                "print(acc.get_balance())"
            ),
            "error_message": (
                "Test 1 FAILED: deposit(-50) should not change balance\n"
                "Test 2 FAILED: withdraw(200) on balance 150 should return "
                "'Insufficient funds' and not change balance\n"
                "Test 3 FAILED: get_balance() after deposit(50) on 100 "
                "should return 150"
            ),
            "correct_output": "150",
            "hint": "Check deposit validation, withdraw condition, and return values."
        },
        {
            "id": "hard_002",
            "difficulty": "hard",
            "description": (
                "Fix the binary search function. "
                "Must pass all 3 unit tests."
            ),
            "buggy_code": (
                "def binary_search(arr, target):\n"
                "    left, right = 0, len(arr)\n"
                "    while left < right:\n"
                "        mid = (left + right) // 2\n"
                "        if arr[mid] == target:\n"
                "            return mid\n"
                "        elif arr[mid] < target:\n"
                "            left = mid\n"
                "        else:\n"
                "            right = mid\n"
                "    return -1\n"
                "print(binary_search([1,3,5,7,9], 5))"
            ),
            "error_message": (
                "Test 1 FAILED: binary_search([1,3,5,7,9], 5) loops forever\n"
                "Test 2 FAILED: binary_search([1,3,5,7,9], 1) loops forever\n"
                "Test 3 FAILED: binary_search([1,3,5,7,9], 10) should return -1"
            ),
            "correct_output": "2",
            "hint": "Check the initial right boundary and how left/right are updated."
        },
        {
            "id": "hard_003",
            "difficulty": "hard",
            "description": (
                "Fix the function that flattens a nested list. "
                "Must pass all 3 unit tests."
            ),
            "buggy_code": (
                "def flatten(lst):\n"
                "    result = []\n"
                "    for item in lst:\n"
                "        if type(item) == list:\n"
                "            result += flatten(item)\n"
                "        else:\n"
                "            result.append(item)\n"
                "    return result\n\n"
                "print(flatten([1, [2, [3, 4]], 5]))"
            ),
            "error_message": (
                "Test 1 FAILED: flatten([1,[2,[3,4]],5]) should return "
                "[1,2,3,4,5]\n"
                "Test 2 FAILED: does not handle tuples\n"
                "Test 3 FAILED: does not handle empty nested lists"
            ),
            "correct_output": "[1, 2, 3, 4, 5]",
            "hint": "Use isinstance() instead of type() to handle subclasses."
        },
    ]


def get_challenge_by_id(challenge_id: str) -> Dict[str, Any]:
    for c in get_challenges():
        if c["id"] == challenge_id:
            return c
    raise ValueError(f"Challenge '{challenge_id}' not found.")


def get_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    return [c for c in get_challenges() if c["difficulty"] == difficulty]