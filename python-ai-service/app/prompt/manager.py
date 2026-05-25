from jinja2 import Template, Environment, StrictUndefined
from sqlalchemy.orm import Session
from app.core.database import WriteSessionLocal
from app.prompt.models import PromptTemplate, PromptStatus, PromptType
from app.common.exceptions.exceptions import ValidationException
from app.core.logger import get_logger

logger = get_logger(__name__)


class PromptManager:
    """Enterprise Prompt Manager — DB persistence, version control, Jinja2 rendering.

    Falls back to builtin templates when MySQL is unavailable.
    """

    BUILTIN_TEMPLATES = {
        "default-system": (
            "You are FlowMind, an enterprise AI assistant. "
            "Answer accurately based on provided context. "
            "If you do not know, say so. "
            "Cite sources when using context documents."
        ),
        "rag-system": (
            "You are an enterprise knowledge assistant. "
            "Answer the user's question based ONLY on the following context documents.\n"
            "If the context does not contain relevant information, say so.\n"
            "Always cite the source document when referencing context.\n\n"
            "Context:\n"
            "{% for doc in context_docs %}"
            "[Source: {{ doc.source }}] {{ doc.content }}\n\n"
            "{% endfor %}"
        ),
        "sql-system": (
            "You are a SQL query assistant. "
            "Given the database schema and user question, generate a valid SQL query.\n"
            "Rules:\n"
            "1. Only SELECT statements allowed\n"
            "2. Always use LIMIT for potentially large result sets\n"
            "3. Use table aliases for readability\n\n"
            "Database Schema:\n"
            "{{ schema }}"
        ),
    }

    def __init__(self):
        self._env = Environment(undefined=StrictUndefined, enable_async=True)
        self._cache: dict[str, PromptTemplate] = {}
        self._db_available = True

    def _try_get_db_template(self, name: str, prompt_type: PromptType | None = None) -> PromptTemplate | None:
        """Try to get template from MySQL, return None if unavailable."""
        if not self._db_available:
            return None
        try:
            db: Session = WriteSessionLocal()
            try:
                q = db.query(PromptTemplate).filter(
                    PromptTemplate.name == name,
                    PromptTemplate.status == PromptStatus.ACTIVE,
                    PromptTemplate.is_deleted == 0,
                )
                if prompt_type:
                    q = q.filter(PromptTemplate.prompt_type == prompt_type)
                return q.order_by(PromptTemplate.version.desc()).first()
            finally:
                db.close()
        except Exception as e:
            self._db_available = False
            logger.warning(f"MySQL unavailable for prompts, using builtins: {e}")
            return None

    def get_template(self, name: str, prompt_type: PromptType | None = None) -> PromptTemplate:
        cache_key = f"{prompt_type.value if prompt_type else 'all'}:{name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try DB first
        tmpl = self._try_get_db_template(name, prompt_type)
        if tmpl:
            self._cache[cache_key] = tmpl
            return tmpl

        # Fallback to builtin
        if name in self.BUILTIN_TEMPLATES:
            tmpl = PromptTemplate(
                name=name,
                prompt_type=prompt_type or PromptType.SYSTEM,
                system_template=self.BUILTIN_TEMPLATES[name],
                status=PromptStatus.ACTIVE,
            )
            return tmpl

        raise ValidationException(f"Prompt template not found: {name}")

    def build_messages(
        self, template_name: str, user_message: str,
        variables: dict | None = None,
        history: list[dict] | None = None,
        prompt_type: PromptType | None = None,
    ) -> list[dict]:
        tmpl = self.get_template(template_name, prompt_type)
        vars_ctx = variables or {}
        vars_ctx["user_message"] = user_message

        try:
            sys_tmpl = self._env.from_string(tmpl.system_template)
            system_content = sys_tmpl.render(**vars_ctx)
        except Exception as e:
            logger.warning(f"System template render error: {e}, using raw template")
            system_content = tmpl.system_template

        try:
            user_tmpl = self._env.from_string(tmpl.user_template)
            user_content = user_tmpl.render(**vars_ctx)
        except Exception:
            user_content = user_message

        messages = [{"role": "system", "content": system_content}]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": user_content})
        return messages

    def invalidate_cache(self, name: str | None = None):
        if name:
            self._cache = {k: v for k, v in self._cache.items() if not k.endswith(f":{name}")}
        else:
            self._cache.clear()

    def list_templates(self, prompt_type: PromptType | None = None) -> list[dict]:
        try:
            db: Session = WriteSessionLocal()
            try:
                q = db.query(PromptTemplate).filter(PromptTemplate.is_deleted == 0)
                if prompt_type:
                    q = q.filter(PromptTemplate.prompt_type == prompt_type)
                results = q.order_by(PromptTemplate.name, PromptTemplate.version.desc()).all()
                return [
                    {"id": t.id, "name": t.name, "type": t.prompt_type.value,
                     "version": t.version, "status": t.status.value}
                    for t in results
                ]
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"List templates failed: {e}")
            return [
                {"id": 0, "name": name, "type": "system", "version": 1, "status": "active"}
                for name in self.BUILTIN_TEMPLATES
            ]

    def create_template(self, data: dict, creator_id: int) -> PromptTemplate:
        db: Session = WriteSessionLocal()
        try:
            tmpl = PromptTemplate(**data, creator_id=creator_id)
            db.add(tmpl)
            db.commit()
            db.refresh(tmpl)
            return tmpl
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


prompt_manager = PromptManager()