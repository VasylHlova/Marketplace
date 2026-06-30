from typing import Any, Protocol

from app.models.user import User


class PolicyProtocol(Protocol):
    def apply(self, current_user: User, resource: Any = None) -> None: ...
