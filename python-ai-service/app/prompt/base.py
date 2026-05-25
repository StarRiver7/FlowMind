# ============================================================
# prompt/base.py — Prompt Layer Abstract
# ============================================================
"""Prompt Layer — manages prompt templates, rendering, and versioning.

Provides:
    - PromptType: enum of prompt categories
    - PromptTemplate: immutable template definition
    - RenderedPrompt: result of rendering a template
    - BasePromptBuilder: abstract interface for prompt assembly
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any


class PromptType(str, Enum):
    SYSTEM = "system"
    RAG = "rag"
    TOOL = "tool"
    SQL = "sql"
    CUSTOM = "custom"


class PromptStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class PromptTemplate:
    """Immutable prompt template definition.

    Fields:
        name: Unique template identifier (e.g. "rag-system")
        prompt_type: Category of prompt
        system_template: Jinja2 template for system message
        user_template: Jinja2 template for user message
        variables: Schema of expected input variables
        version: Monotonic version number
        status: Lifecycle status
        model_constraint: Optional provider/model restriction
    """
    name: str
    prompt_type: PromptType
    system_template: str
    user_template: str = "{{ user_message }}"
    variables: dict[str, dict] = field(default_factory=dict)
    version: int = 1
    status: PromptStatus = PromptStatus.ACTIVE
    model_constraint: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class RenderedPrompt:
    """Result of rendering a PromptTemplate with variables."""
    messages: list[dict[str, str]]
    template_name: str
    template_version: int


class BasePromptBuilder(ABC):
    """Abstract contract for prompt assembly and rendering.

    Implementations may source templates from:
        - A database (production)
        - Static built-in constants (development)
        - External template service (enterprise)
    """

    @abstractmethod
    def get_template(
        self,
        name: str,
        *,
        prompt_type: Optional[PromptType] = None,
        version: Optional[int] = None,
    ) -> PromptTemplate:
        """Retrieve a prompt template by name and optional type/version.

        Raises:
            ValueError: If template not found
        """
        ...

    @abstractmethod
    def render(
        self,
        template: PromptTemplate,
        variables: dict[str, Any],
    ) -> RenderedPrompt:
        """Render a template with provided variables.

        Uses Jinja2 with StrictUndefined to catch missing variables.
        Supports async rendering for templates that need external data.
        """
        ...

    @abstractmethod
    def build_messages(
        self,
        template_name: str,
        user_message: str,
        *,
        variables: Optional[dict[str, Any]] = None,
        history: Optional[list[dict[str, str]]] = None,
        prompt_type: Optional[PromptType] = None,
    ) -> RenderedPrompt:
        """High-level: get template, render with variables, inject history.

        This is the primary entry point for Agent nodes.
        """
        ...

    @abstractmethod
    def list_templates(
        self,
        *,
        prompt_type: Optional[PromptType] = None,
    ) -> list[PromptTemplate]:
        """List available templates, optionally filtered by type."""
        ...
