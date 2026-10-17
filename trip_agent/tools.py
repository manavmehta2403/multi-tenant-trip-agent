from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    allowed_tools: frozenset[str]
    config: dict

class ToolRegistry:
    """Shared code, not shared state: every call is executed with the caller's TenantContext,
    and tools only ever see data scoped to that tenant."""
    def __init__(self):
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str):
        def deco(fn):
            self._tools[name] = fn
            return fn
        return deco

    def call(self, ctx: TenantContext, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise KeyError(f"unknown tool {name}")
        if name not in ctx.allowed_tools:
            raise PermissionError(f"tool {name} not enabled for tenant {ctx.tenant_id}")
        return self._tools[name](ctx, **kwargs)

class TenantStore:
    """Toy data store whose every read is keyed by tenant — no API exists to read across tenants."""
    def __init__(self, data: dict[str, list[dict]]):
        self._data = data
    def for_tenant(self, tenant_id: str) -> list[dict]:
        return list(self._data.get(tenant_id, []))
