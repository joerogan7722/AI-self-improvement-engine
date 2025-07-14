# AI Self-Improvement Engine

This project is a Python-based, self-improving AI engine designed to autonomously enhance its own codebase. It features a modular, role-based architecture that allows for a clear separation of concerns and easy extensibility.

## Core Features

*   **Role-Based Architecture**: The engine's functionality is divided into distinct roles, each responsible for a specific part of the self-improvement cycle:
    *   `ProblemIdentificationRole`: Identifies areas for improvement in the codebase.
    *   `RefineRole`: Generates patches to address the identified problems.
    *   `TestRole`: Generates and runs tests to validate the changes.
    *   `SelfReviewRole`: Reviews the applied changes for quality and correctness.
*   **Learning and Adaptation**: The engine learns from its past experiences. A `LearningLog` records the outcome of every improvement cycle, and this data is fed back into the `RefineRole` to improve future patch generation.
*   **Automated Test Generation**: The `TestRole` automatically generates new `pytest` tests for the code modifications made by the `RefineRole`, ensuring that the test suite evolves alongside the codebase.
*   **Configuration-Driven**: The engine is highly configurable via `config/engine_config.yaml`, allowing for easy modification of roles, prompts, and other parameters.
*   **Robustness**: The engine uses a `SnapshotStore` to save its state, allowing it to resume interrupted improvement cycles.

## Getting Started

1.  **Installation**:
    ```bash
    pip install -e .
    ```
2.  **Configuration**:
    *   Copy `config/engine_config.yaml.example` to `config/engine_config.yaml`.
    *   Update the configuration file with your specific settings (e.g., API keys for the model).
3.  **Running the Engine**:
    ```bash
    ai-self-ext-engine run
    ```

## Future Work

The following high-priority items are planned for future development:

*   **Refine the Plugin Architecture**: Improve the plugin system to make it more extensible.
*   **Explore Parallel Goal Execution**: Investigate the possibility of executing independent goals in parallel to improve performance.
*   **Adopt a Dependency Management Tool**: Use a tool like `poetry` or `pip-tools` to manage dependencies more effectively.
