# Codex Operator Commands

Short operator commands must be interpreted through
`docs/ai/CODEX_WORKFLOW.md`.

## `План`

Reads project state and proposes 3-5 next tasks ranked by value. Does not
change files. Use when choosing the next task.

## `План подробнее N`

Expands task `N` into scope, checks, done criteria, and commit message. Does
not change files. Use before approving a task.

## `Утверждаю задачу N`

Records the selected task in `CODEX_CURRENT.md` with `status: approved`.
Changes state files only. Use when selecting a planned task.

## `Выполняй`

Runs the approved task through the One-Task Loop, checks it, commits once, and
stops. Changes only files allowed by the approved task. Use after approval.

## `Выполняй без коммита`

Runs the approved task and checks, then stops before commit. Changes allowed
task files. Use when you want to review the diff first.

## `Коммить`

Commits the approved scoped changes only after checks passed or skipped checks
are explained. Changes git history only. Use after `Выполняй без коммита`.

## `Статус`

Reports current status, approved task, phase, changed files, checks, blockers,
and next action. Does not change files. Use to inspect the loop state.

## `Стоп`

Stops current work and marks `CODEX_CURRENT.md` as `stopped`. Changes state
files only. Use when pausing unfinished work.

## `Отмени текущую`

Marks `CODEX_CURRENT.md` as `cancelled` without deleting changes unless told.
Changes state files only. Use to abandon the current task.

## `Продолжай текущую`

Reads `CODEX_CURRENT.md` and continues only the approved or stopped task.
Changes allowed task files. Use to resume a paused loop.

## `Советник`

Reads project state, assesses drift and stalled work, gives 3 management or
research suggestions, and recommends one next operator step. Does not change
files. Use for strategic review.

## `Аудит`

Checks consistency across Codex control docs and reports stale or contradictory
state. Does not change files. Use before relying on the workflow state.
