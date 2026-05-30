# Codex Workflow

## Operator Commands

Short operator commands are authoritative. If the operator writes one of the
commands below, Codex must interpret it according to this section instead of
asking for a long prompt.

If a command is unclear, Codex must ask one short clarifying question before
starting implementation. If a command may expand scope, Codex must stop and ask
for confirmation. Codex must not automatically move from `План` to `Выполняй`,
and must not automatically move from one task to the next.

### Planning commands

#### `План`

Codex must:

- read `PROJECT_GOAL.md`, `CODEX_TASKS.md`, `CODEX_PLAN.md`,
  `CODEX_CURRENT.md`, and `docs/ai/CODEX_WORKFLOW.md`;
- not change files;
- propose 3-5 next tasks;
- sort tasks by scientific/project value;
- for each task, include:
  - goal;
  - expected result;
  - why this is not work for work's sake;
  - files likely touched;
  - definition of done;
  - main check;
  - negative checks;
  - risk;
- stop and wait for the operator's choice.

#### `План подробнее N`

Codex must expand task `N` without changing files:

- exact task statement;
- scope boundaries;
- what not to do;
- files that may be touched;
- readiness criteria;
- checks;
- expected commit message.

#### `Утверждаю задачу N`

Codex must:

- write the selected task to `CODEX_CURRENT.md`;
- set `status: approved`;
- record allowed files, definition of done, checks, and stop conditions;
- not start implementation until the operator says `Выполняй`.

### Execution commands

#### `Выполняй`

Codex must execute the approved task through the One-Task Loop:

1. Clarify the goal.
2. Quickly estimate the solution.
3. Implement.
4. Check the main scenario.
5. Check a couple of negative scenarios.
6. Commit.
7. Briefly describe the result.
8. Stop.

After execution, Codex must:

- update `CODEX_TASKS.md`;
- update `CODEX_CURRENT.md`;
- update `CODEX_SESSION_LOG.md`;
- make exactly one commit;
- stop and not take the next task.

#### `Выполняй без коммита`

Codex must execute the task and checks, but stop before committing.

The final message must include:

- what changed;
- which checks passed;
- whether the commit is ready;
- suggested commit message.

#### `Коммить`

Codex may commit only if:

- there is an approved task;
- changes match the approved scope;
- checks have already passed, or Codex explicitly documents why some checks
  were not run.

#### `Статус`

Codex must briefly show, without changing files:

- current status;
- approved task;
- current phase;
- files changed;
- checks already run;
- blockers;
- next required operator action.

#### `Стоп`

Codex must:

- stop current work;
- update `CODEX_CURRENT.md` with `status: stopped`;
- briefly describe what was done and what remains;
- not commit unfinished work without a separate command.

#### `Отмени текущую`

Codex must:

- move `CODEX_CURRENT.md` to `status: cancelled`;
- explain what was cancelled;
- not delete changes automatically unless explicitly instructed.

#### `Продолжай текущую`

Codex must:

- read `CODEX_CURRENT.md`;
- continue only the current `approved` or `stopped` task;
- not take a new task;
- follow the One-Task Loop.

### Default rule

If the operator writes a short command from this list, Codex must interpret it
according to `Operator Commands`.

If the command is unclear, Codex must ask a short clarifying question instead
of starting implementation.

If the command can expand scope, Codex must stop and ask for confirmation.

Codex must not automatically move from `План` to `Выполняй`.

Codex must not automatically move from one task to the next.
