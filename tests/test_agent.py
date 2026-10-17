import pytest
from trip_agent.agent import TripAgent, build_registry
from trip_agent.intent import consensus, rule_extractor
from trip_agent.state import Stage, TripState, transition
from trip_agent.tools import TenantContext, TenantStore

STORE = TenantStore({
    "brand_a": [{"name": "Lisbon Explorer", "destination": "Lisbon", "min_nights": 2, "base_price": 50}],
    "brand_b": [{"name": "Lisbon Secret", "destination": "Lisbon", "min_nights": 2, "base_price": 80}],
})
A = TenantContext("brand_a", frozenset({"search_packages"}), {"markup": 0.1})
B = TenantContext("brand_b", frozenset({"search_packages"}), {})

def test_extracts_slots():
    assert rule_extractor("3 nights to Lisbon for two people") == {"nights": 3, "destination": "Lisbon", "travellers": 2}

def test_consensus_drops_conflicts():
    agreed, conflicts = consensus("x", lambda t: {"nights": 3, "destination": "Rome"}, lambda t: {"nights": 4, "destination": "Rome"})
    assert agreed == {"destination": "Rome"} and conflicts == ["nights"]

def test_full_flow_and_tenant_pricing():
    agent = TripAgent(build_registry(STORE))
    s = TripState("brand_a")
    s, r = agent.step(s, A, "Trip to Lisbon please")
    assert "nights" in r
    s, r = agent.step(s, A, "3 nights for two people")
    assert s.stage == Stage.CONFIRMING
    s, r = agent.step(s, A, "yes")
    assert s.stage == Stage.DONE and r == "Found 1 package(s)."
    assert agent.registry.call(A, "search_packages", destination="Lisbon", nights=3, travellers=2)[0]["price"] == 330.0

def test_tenants_never_see_each_others_data():
    reg = build_registry(STORE)
    names_a = {p["name"] for p in reg.call(A, "search_packages", destination="Lisbon", nights=3, travellers=1)}
    names_b = {p["name"] for p in reg.call(B, "search_packages", destination="Lisbon", nights=3, travellers=1)}
    assert names_a == {"Lisbon Explorer"} and names_b == {"Lisbon Secret"}

def test_session_tenant_mismatch_rejected():
    with pytest.raises(PermissionError):
        TripAgent(build_registry(STORE)).step(TripState("brand_a"), B, "hi")

def test_tool_not_enabled_for_tenant():
    with pytest.raises(PermissionError):
        build_registry(STORE).call(TenantContext("brand_a", frozenset(), {}), "search_packages", destination="x", nights=1, travellers=1)

def test_illegal_transition_and_missing_slots():
    with pytest.raises(ValueError):
        transition(TripState("t"), Stage.DONE)
    with pytest.raises(ValueError):
        transition(TripState("t"), Stage.CONFIRMING)

def test_inferred_value_never_overwrites_user_value():
    s = TripState("t").merge({"nights": 3}, "user").merge({"nights": 5}, "inferred")
    assert s.slots["nights"] == 3
