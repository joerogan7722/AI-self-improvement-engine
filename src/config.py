from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ValidationError, validator

class EngineConfig(BaseModel):
    """
    Configuration schema for the AI Self-Extending Engine.
    """
    code_dir: str = Field(..., description="Path to the codebase directory.")
    memory_path: str = Field(".sim_memory", description="Path to the memory/snapshot directory.")
    max_cycles: int = Field(1, description="Maximum number of improvement cycles to run.")
    goals_path: str = Field("goals.json", description="Path to the goals file.")
    
    # Model settings
    generator_model: str = Field("gemini-2.5-flash", description="Model for initial content generation.")
    critic_model: str = Field("gemini-2.5-flash", description="Model for critique generation.")
    refiner_model: str = Field("gemini-2.5-flash", description="Model for code refinement.")
    meta_critic_model: str = Field("gemini-2.5-flash", description="Model for meta-critique (actionability check).")

    # Role sequencing
    role_sequence: List[str] = Field(
        ["ProblemIdentificationRole", "RefineRole", "TestRole", "SelfReviewRole"],
        description="Ordered list of roles to execute in each cycle."
    )

    # Prompt templates
    prompts_dir: str = Field("prompts", description="Directory containing prompt templates, relative to project root.")

    # Redaction for logging (from critique_refine)
    redact_logs: bool = Field(False, description="Whether to redact sensitive information from logs.")
    redaction_config: Dict[str, Any] = Field({}, description="Configuration for log redaction.")

    # Strategy (from critique_refine)
    strategy: Optional[str] = Field(None, description="Name of the strategy to use from strategies.yaml.")

    # Internal versioning for config schema (for future compatibility)
    config_version: Literal["1.0.0"] = Field("1.0.0")

    @validator('max_cycles')
    def validate_max_cycles(cls, v):
        if v <= 0:
            raise ValueError('max_cycles must be a positive integer')
        return v
