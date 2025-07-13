### Deep Dive: `SelfImprovementModule.improve()` Mapping

Below is a line-by-line extraction of the `improve()` method from `src/god_engine/self_improvement.py`, annotated with how each section will map to our new `Engine` and `Role` abstractions.

```python
# File: src/god_engine/self_improvement.py

class SelfImprovementModule:
    def __init__(self, config):
        self.config = config
        self.memory = load_json(config['memory_path'])
        self.goals = GoalManager(config['goals_path'])
        self.engine = ExperimentationEngine(config)
        self.improver = ImprovementEngine(config)
        self.rule_engine = RuleEngine(config)

    def improve(self):
        # 1) Loop over cycles
        for cycle in range(self.config['max_cycles']):
            # 2) Fetch next goal
            goal = self.goals.next_goal()
            if not goal:
                break

            # 3) Skip if already in memory
            if goal.id in self.memory:
                continue

            # 4) Identify tasks/todos from goal description
            todos = self.engine.generate_todos(goal.description)

            # 5) Generate patch from todos
            patch = self.improver.create_patch(
                code_dir=self.config['code_dir'],
                todos=todos
            )

            # 6) Apply patch via git
            git_apply(patch, cwd=self.config['code_dir'])

            # 7) Run tests and evaluate
            test_results = run_tests(self.config['code_dir'])

            if not test_results.passed:
                git_reset(self.config['code_dir'])

            # 8) Evaluate acceptance via rules
            accepted = self.rule_engine.evaluate(
                goal, todos, test_results
            )

            # 9) Record in memory
            self.memory[goal.id] = {
                'cycle': cycle,
                'todos': todos,
                'patch': patch,
                'tests': test_results,
                'accepted': accepted
            }
            save_json(self.memory, self.config['memory_path'])

            # 10) Stop if not accepted
            if not accepted:
                break
```

---

## Mapping to New Architecture

| Original Step | Code Snippet | New Role/Component |
| ------------- | ------------ | ------------------ |
|               |              |                    |

| **Initialization**          | `__init__` sets up `memory`, `goals`, `engine`, etc.   | Moved to `Engine.__init__`: initialize `GoalManager`, `SnapshotStore`, and load `Role` plugins. |
| --------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| **1. Loop**                 | `for cycle in range(...)`                              | `Engine.run_cycles()` loop over `config.max_cycles`.                                            |
| **2. Fetch Goal**           | `goal = self.goals.next_goal()`                        | `context.goal = GoalManager.next_goal()` within each cycle.                                     |
| **3. Skip Duplicate**       | `if goal.id in self.memory: continue`                  | `SnapshotStore.has(goal)` check before roles.                                                   |
| **4. Identify Tasks/Todos** | `todos = self.engine.generate_todos(goal.description)` | `ProblemIdentificationRole.run(context)` sets `context.todos`.                                  |
| **5. Generate Patch**       | `patch = self.improver.create_patch(...)`              | `RefineRole.run(context)` uses `ModelClient` + `CodePatcher`.                                   |
| **6. Apply Patch**          | `git_apply(patch, cwd=...)`                            | Inside `RefineRole`, call `VCSManager.apply_patch()`.                                           |
| **7. Run Tests**            | `test_results = run_tests(...)`                        | `TestRole.run(context)` invokes `Plugin.test()`.                                                |
| **8. Evaluate Acceptance**  | `accepted = self.rule_engine.evaluate(...)`            | `SelfReviewRole.run(context)` sets `context.accepted`.                                          |
| **9. Record Memory**        | `self.memory[...] = ...` + `save_json(...)`            | `SnapshotStore.record(context)` writes metadata & artifacts.                                    |
| **10. Termination Check**   | `if not accepted: break`                               | `Engine` checks `context.accepted` to break loop.                                               |

---

### Notes & Considerations

- **Engine vs Roles**: Most steps map cleanly to discrete Roles; only loop control and memory management remain in the core `Engine`.
- **Error Handling**: We’ll wrap each `role.run()` in try/except inside `Engine` to catch and retry or abort gracefully.
- **Context Object**: We’ll define a `Context` dataclass containing `goal`, `todos`, `code_dir`, `patch`, `test_results`, and flags like `accepted` and `should_abort`.
- **Abstract Interfaces**: Create `Role` and `Plugin` ABCs now to ensure type consistency as we port functionality.

---

*Next up: Define the **`Context`** dataclass and draft the **`Engine`** class skeleton based on this mapping.*

