from __future__ import annotations
from .intent import consensus, rule_extractor, Extractor
from .state import Stage, TripState, transition
from .tools import TenantContext, ToolRegistry, TenantStore

def build_registry(store: TenantStore) -> ToolRegistry:
    reg = ToolRegistry()

    @reg.register("search_packages")
    def search_packages(ctx: TenantContext, destination: str, nights: int, travellers: int):
        markup = ctx.config.get("markup", 0.0)
        return [
            {**p, "price": round(p["base_price"] * nights * travellers * (1 + markup), 2)}
            for p in store.for_tenant(ctx.tenant_id)
            if p["destination"].lower() == destination.lower() and p["min_nights"] <= nights
        ]
    return reg

class TripAgent:
    def __init__(self, registry: ToolRegistry, second_extractor: Extractor = rule_extractor):
        self.registry, self.second = registry, second_extractor

    def step(self, state: TripState, ctx: TenantContext, text: str) -> tuple[TripState, str]:
        if state.tenant_id != ctx.tenant_id:
            raise PermissionError("session tenant mismatch")
        if state.stage == Stage.CONFIRMING:
            if text.strip().lower() in {"yes", "y", "confirm"}:
                state = transition(state, Stage.SEARCHING)
                res = self.registry.call(ctx, "search_packages", **{k: state.slots[k] for k in ("destination", "nights", "travellers")})
                state = transition(state, Stage.DONE)
                return state, f"Found {len(res)} package(s)." if res else "No packages match — want to change something?"
            state = transition(state, Stage.COLLECTING)
        values, conflicts = consensus(text, rule_extractor, self.second)
        state = state.merge(values, "user")
        if conflicts:
            return state, f"Just to be sure — could you confirm your {', '.join(conflicts)}?"
        if state.missing():
            return state, f"Got it. What about your {state.missing()[0]}?"
        state = transition(state, Stage.CONFIRMING)
        s = state.slots
        return state, f"{s['nights']} nights in {s['destination']} for {s['travellers']}. Search now?"
