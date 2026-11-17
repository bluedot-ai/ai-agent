from dataclasses import dataclass, field
from .api_client import ApiClient, BackendError
from .observability import Audit

@dataclass
class AgentContext:
    training_id: int
    api_client: ApiClient = field(repr=False)
    audit: Audit
    calls: int = 0
    successful: set = field(default_factory=set)
    stage_cache: dict | None = None

    async def preflight(self):
        if self.api_client.training_id != self.training_id:
            raise BackendError("SCOPE_MISMATCH")
        me = await self.api_client.me()
        role = me.get("role")
        if role not in {"TRAINEE", "REVIEWER", "ADMIN"}:
            raise BackendError("INVALID_ROLE")
        self.audit.role = role
        t = await self.api_client.training()
        if t["id"] != self.training_id:
            raise BackendError("SCOPE_MISMATCH")
