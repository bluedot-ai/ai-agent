import json
from dataclasses import dataclass, field
from uuid import uuid4

@dataclass
class Audit:
    training_id: int
    role: str = "UNKNOWN"
    run_id: str = field(default_factory=lambda: str(uuid4()))
    events: list = field(default_factory=list)

    def record(self, kind, **fields):
        # Only metadata is accepted. Never accept messages, arguments, bodies or exceptions.
        allowed = {"tool", "elapsed_ms", "http_status", "status", "model_calls",
                   "input_tokens", "output_tokens"}
        row = dict(run_id=self.run_id, training_id=self.training_id,
                   role=self.role, kind=kind)
        row.update({k: v for k, v in fields.items() if k in allowed})
        self.events.append(row)

    def dump(self):
        return "\n".join(json.dumps(x, ensure_ascii=False) for x in self.events)

    def save(self, path):
        import os
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a") as out:
            out.write(self.dump() + "\n")
