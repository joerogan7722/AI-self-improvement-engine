# src/roles/__init__.py

from .problem_identification import ProblemIdentificationRole
from .refine import RefineRole
from .test import TestRole
from .self_review import SelfReviewRole

# Expose all roles for dynamic loading
__all__ = [
    "ProblemIdentificationRole",
    "RefineRole",
    "TestRole",
    "SelfReviewRole",
]
