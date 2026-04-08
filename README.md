---
title: Code Debug Env
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - code-debugging
  - reinforcement-learning
---

#  Code Debug Environment (OpenEnv)

This project is an OpenEnv-compatible environment designed to simulate how an AI agent can **debug Python code step by step**.

Instead of solving everything in one attempt, the agent is given **buggy code, error messages, and hints**, and it gradually improves the code across multiple steps — just like how real debugging works.

---

##  What this project does

- Allows an AI agent to fix broken Python code  
- Supports multiple difficulty levels: **easy, medium, hard**  
- Provides rewards based on how correct the solution is  
- Encourages step-by-step improvement instead of one-shot answers  
- Simulates real-world debugging scenarios  

---

##  How the environment works

###  What the agent receives (Observation)

At each step, the agent gets:

- `challenge_id` → identifies the problem  
- `difficulty` → easy / medium / hard  
- `description` → explains the task  
- `buggy_code` → the incorrect code  
- `error_message` → what’s going wrong  
- `hint` → optional guidance  
- `step` → current attempt number  
- `max_steps` → maximum attempts allowed  

---

###  What the agent does (Action)

The agent responds by submitting a corrected version of the code:

```python
{
  "fixed_code": "your corrected python code here"
}

