from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ValidationError, validator

class EngineSectionConfig(BaseModel):
    code_dir: str = Field("./src", description="Path to the codebase directory relative to project root.")
    max_cycles: int = Field(3, description="Maximum number of improvement cycles to run.")
    memory_path: str = Field("./memory", description="Path to the memory/snapshot directory relative to project root.")
    goals_path: str = Field("goals.json", description="Path to the goals file.")
    prompts_dir: str = Field("prompts", description="Directory containing prompt templates, relative to project root.")

class ModelSectionConfig(BaseModel):
    api_key_env: str = Field(..., description="Environment variable name for the API key.")
    model_name: str = Field("gemini-2.5-flash", description="Default model name to use.")

class RoleConfig(BaseModel):
    module: str = Field(..., description="Module path for the role, e.g., 'roles.problem_identification'.")
    class_name: str = Field(..., alias='class', description="Class name of the role within the module, e.g., 'ProblemIdentificationRole'.")
    prompt_path: str = Field(..., description="Path to the prompt template file relative to prompts_dir.")

class PluginConfig(BaseModel):
    entry_point: str = Field(..., description="Full import path to the plugin class, e.g., 'plugins.python.PythonPlugin'.")

class LoggingConfig(BaseModel):
    level: str = Field("INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).")
    format: str = Field("json", description="Logging output format (json or plain).")
    log_file: Optional[str] = Field(None, description="Optional path to a log file. If not provided, logs go to stderr.")

class MainConfig(BaseModel):
    """
    Main configuration schema for the AI Self-Extending Engine.
    """
    version: Literal[1] = Field(1, description="Version of the configuration schema.")
    engine: EngineSectionConfig = Field(..., description="Engine core settings.")
    model: ModelSectionConfig = Field(..., description="Model client settings.")
    roles: List[RoleConfig] = Field(..., description="List of roles to execute in order.")
    plugins: Dict[str, PluginConfig] = Field({}, description="Dictionary of plugins, keyed by name.")
    logging: LoggingConfig = Field(..., description="Logging configuration.")

    @validator('engine')
    def validate_engine_max_cycles(cls, v):
        if v.max_cycles <= 0:
            raise ValueError('engine.max_cycles must be a positive integer')
        return v

    class Config:
        validate_by_name = True # Allow 'class' to be used in RoleConfig
