from dataclasses import dataclass, field

from app.policies.common import AllowAllPolicy
from app.policies.protocols import PolicyProtocol


@dataclass
class PolicySet:
    read: PolicyProtocol = field(default_factory=AllowAllPolicy)
    update: PolicyProtocol = field(default_factory=AllowAllPolicy)
    delete: PolicyProtocol = field(default_factory=AllowAllPolicy)
    cancel: PolicyProtocol = field(default_factory=AllowAllPolicy)
    complete: PolicyProtocol = field(default_factory=AllowAllPolicy)
    item: PolicyProtocol = field(default_factory=AllowAllPolicy)
