# src/core/__init__.py

from .engine import Engine
from .role import Context, Role, RoleType # Context is defined in role.py, not engine.py
from .plugin import Plugin
# GoalManager is not exposed directly in __init__.py, but Goal is
from ..goal_manager import Goal
from ..model_client import ModelClient, ModelCallError
