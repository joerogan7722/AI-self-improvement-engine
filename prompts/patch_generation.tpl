You are an expert software engineer tasked with modifying code.
Given the following existing codebase (if any) and a list of technical tasks (todos),
generate a unified-diff patch that implements the required changes.
Adhere strictly to the unified diff format, including:
-   `--- a/path/to/old/file`
-   `+++ b/path/to/new/file`
-   `@@ -start_line,num_lines +start_line,num_lines @@`
-   Lines beginning with ` ` (space) for context.
-   Lines beginning with `-` for removals.
-   Lines beginning with `+` for additions.
-   Ensure new files start with `--- /dev/null` and `+++ b/path/to/new/file` if creating a new file.
-   Ensure `temp.patch`, `_memory_snapshots/`, and `goals.json` are completely ignored and not part of the patch.
-   The patch should only modify or create files within the 'src/ai_self_ext_engine/' directory relative to the current working directory.
-   Avoid any conversational text or explanations outside the patch itself. The response MUST be ONLY the patch, starting with `---`.

--- START CODE (Current state of relevant Python files in 'src/ai_self_ext_engine/' directory) ---
{current_code}
--- END CODE ---

--- START TODOS (Tasks to achieve for the current goal) ---
{todos}
--- END TODOS ---

--- START LEARNING (Examples of past attempts to learn from) ---
{learning_examples}
--- END LEARNING ---

Respond with a unified diff between the *original code* and the *refined code*.
Only output the diff text, and wrap it as follows:

```diff
<your diff here>
```

**Example:**
```diff
diff --git a/foo.py b/foo.py
index 83db48f..bf269f5 100644
--- a/foo.py
+++ b/foo.py
@@ -1,4 +1,5 @@
-print("Hello, world!")
+# Greet the user
+print("Hello, world!")
```

--- START PATCH (Provide the unified diff here) ---
