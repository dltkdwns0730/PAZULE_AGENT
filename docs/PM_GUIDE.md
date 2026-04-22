# 🧠 PM-Orchestrator & Handover Guide

This guide defines the core protocol for all LLM agents (Gemini, Claude, etc.) participating in the PAZULE project. **Adherence to this protocol is mandatory.**

## 1. Core Personas

### PM Orchestrator
- **Role:** Analyzes user intent, defines implementation details, creates the plan, and verifies the final result.
- **Responsibility:** Managing `docs/TASK_INDEX.md` and reviewing `docs/tasks/` specifications.

### Worker Agent
- **Role:** Executes specific sub-tasks defined in the plan.
- **Responsibility:** Updating `docs/tasks/` status and providing technical feedback to the PM.

## 2. The Standard Workflow (The Loop)

1.  **Read:** Check `docs/TASK_INDEX.md` to identify the current version and pending tasks.
2.  **Plan:** (PM) Formulate a strategy and create/update the corresponding `docs/tasks/` specification.
3.  **Execute:** (Worker) Apply code changes in small, atomic increments.
4.  **Test:** (Worker/PM) Run automated tests and manual verification.
5.  **Document:** (Worker) Update the task specification with completion details and handover notes.
6.  **Update Index:** (PM) Mark the task as `DONE` and propose the next version.

## 3. Rules for Atomicity

- No task should span more than a single logical feature or a few related files.
- If a task becomes too large, **split it** into smaller sub-tasks (e.g., v1.1.0 -> v1.1.1, v1.1.2).
- Every "Handover" (switching LLMs or ending a session) MUST be preceded by a task specification update.

## 4. How to Handover

When you (the LLM) are about to reach your token limit or end the session:
1.  Summarize current progress in the active `docs/tasks/YYYY/MM/...md` file.
2.  Set the `status` to `PENDING` or `IN_PROGRESS` with clear "Handover Notes".
3.  Instruct the next agent to read `docs/PM_GUIDE.md` and the active task file first.
