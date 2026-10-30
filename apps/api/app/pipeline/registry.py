"""Phase 3: Step registry for declarative step discovery."""

from pydantic import BaseModel

from .base_step import Step

# Default step order for a complete pipeline
DEFAULT_STEP_ORDER = [
    "analyze_repo",
    "generate_outline",
    "generate_content",
    "refine",
    "save_tutorial",
]

# Registry: step_type -> Step class
STEP_REGISTRY: dict[str, type[Step]] = {}

# Registry: step_type -> (Input class, Output class)
STEP_CONTRACTS: dict[str, tuple[type[BaseModel], type[BaseModel]]] = {}


def register_step(
    step_type: str,
    input_class: type[BaseModel],
    output_class: type[BaseModel],
):
    """Decorator to register a step class."""

    def decorator(cls: type[Step]) -> type[Step]:
        STEP_REGISTRY[step_type] = cls
        STEP_CONTRACTS[step_type] = (input_class, output_class)
        return cls

    return decorator


def get_step_class(step_type: str) -> type[Step] | None:
    """Get the step class for a given step type."""
    return STEP_REGISTRY.get(step_type)


def get_step_contract(step_type: str) -> tuple[type[BaseModel], type[BaseModel]] | None:
    """Get the input/output contract for a given step type."""
    return STEP_CONTRACTS.get(step_type)


def get_all_step_types() -> list[str]:
    """Get all registered step types in order."""
    return [t for t in DEFAULT_STEP_ORDER if t in STEP_REGISTRY]


# =============================================================================
# Actual Step Implementations (to be created separately)
# =============================================================================

# These are placeholders - actual implementations will be added in subsequent files
# from .steps.analyze_repo_step import AnalyzeRepoStep
# from .steps.generate_outline_step import GenerateOutlineStep
# from .steps.generate_content_step import GenerateContentStep
# from .steps.refine_step import RefineStep
# from .steps.save_tutorial_step import SaveTutorialStep

# For now, let's just have the registry defined and add implementations below
