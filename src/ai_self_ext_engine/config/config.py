# src/ai_self_ext_engine/config/config.py
# Default configuration settings for the AI Self-Extending Engine.
# This can be used as a template for engine_config.yaml.

default_config_yaml = """
version: 1
engine:
  code_dir: ./src
  max_cycles: 3
  memory_path: ./memory
  goals_path: goals.json
  prompts_dir: prompts
model:
  api_key_env: GEMINI_API_KEY
  model_name: gemini-2.5-flash
roles:
  - module: ai_self_ext_engine.roles.problem_identification
    class: ProblemIdentificationRole
    prompt_path: problem_identification.tpl
  - module: ai_self_ext_engine.roles.refine
    class: RefineRole
    prompt_path: patch_generation.tpl
  - module: ai_self_ext_engine.roles.test
    class: TestRole
    prompt_path: N/A # TestRole does not use a prompt template directly
  - module: ai_self_ext_engine.roles.self_review
    class: SelfReviewRole
    prompt_path: N/A # SelfReviewRole does not use a prompt template directly
plugins: {}
logging:
