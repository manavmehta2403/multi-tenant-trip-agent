from __future__ import annotations
from dataclasses import dataclass, field, replace
from enum import Enum

class Stage(str, Enum):
    COLLECTING = "collecting"
    CONFIRMING = "confirming"
    SEARCHING = "searching"
    DONE = "done"

REQUIRED = ("destination", "nights", "travellers")

@dataclass(frozen=True)
class TripState:
    tenant_id: str
    stage: Stage = Stage.COLLECTING
    slots: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)  # slot -> "user" | "inferred"

    def missing(self) -> list[str]:
        return [s for s in REQUIRED if s not in self.slots]

    def merge(self, values: dict, source: str) -> "TripState":
        slots, prov = dict(self.slots), dict(self.provenance)
        for k, v in values.items():
            # provenance rule: an inferred value never overwrites something the user said
            if prov.get(k) == "user" and source != "user":
                continue
            slots[k], prov[k] = v, source
        return replace(self, slots=slots, provenance=prov)

ALLOWED = {
    Stage.COLLECTING: {Stage.COLLECTING, Stage.CONFIRMING},
    Stage.CONFIRMING: {Stage.COLLECTING, Stage.SEARCHING},
    Stage.SEARCHING: {Stage.DONE, Stage.COLLECTING},
    Stage.DONE: {Stage.COLLECTING},
}

def transition(state: TripState, to: Stage) -> TripState:
    if to not in ALLOWED[state.stage]:
        raise ValueError(f"illegal transition {state.stage.value} -> {to.value}")
    if to in (Stage.CONFIRMING, Stage.SEARCHING) and state.missing():
        raise ValueError(f"cannot {to.value}: missing {state.missing()}")
    return replace(state, stage=to)
