"""Trial isolation, evidence-to-window semantics and real stock/work lifecycle."""

import uuid

import pytest
from sqlalchemy import select

from fleet_maintenance.domain.contracts.demo import (
    HistoryImport,
    TrialCatalogResponse,
    TrialRequest,
)
from fleet_maintenance.persistence.models import Aircraft, Assessment, Part
from fleet_maintenance.services import customer_trials
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.arrivals import record_arrival
from fleet_maintenance.services.inspection import plan_commitment
from fleet_maintenance.services.planning import planning_snapshot, propose_plan, restore_source
from fleet_maintenance.services.reservations import update_work


@pytest.fixture
def trial_catalog(monkeypatch):
    history = HistoryImport.model_validate(
        {
            "source_version": "test-only",
            "engine_identity": "NASA_CMAPSS:FD001:train:1",
            "rows": [{"cycle": cycle, "values": [1.0] * 24} for cycle in range(1, 41)],
        }
    )
    monkeypatch.setattr(
        customer_trials,
        "catalog",
        lambda session: TrialCatalogResponse(
            available=True,
            reason="test fixture",
            model_id="test-model",
            history=history,
            source_sha256="test-source",
        ),
    )


def request(**changes):
    return TrialRequest.model_validate(
        {
            "id": f"trial-{uuid.uuid4().hex}",
            "aircraft_label": "Test customer's aircraft",
            "cutoff_cycle": 40,
            "cycles_per_day": 12.0,
            "duration_slots": 2,
            "deadline_slot": 14,
            "spare_on_hand": 1,
            "arrival_slot": 3,
            **changes,
        }
    )


def add_assessment(session, trial, *, lower=40.0, state="available"):
    # Controlled evidence fixture tests application policy, not model accuracy.
    assessment = Assessment(
        id=f"asm-{uuid.uuid4().hex}",
        component_id=trial.component_id,
        model_version=trial.model_id,
        input_version=trial.import_id,
        cutoff_cycle=trial.cutoff_cycle,
        state=state,
        lower_cycles=lower if state == "available" else None,
        estimate_cycles=lower + 10 if state == "available" else None,
        upper_cycles=lower + 20 if state == "available" else None,
    )
    session.add(assessment)
    session.commit()
    return assessment


def test_trials_keep_independent_stock_crew_and_default_plan(isolated_session, trial_catalog):
    s = isolated_session
    fleet_before = planning_snapshot(s)
    a = customer_trials.create_trial(s, request(), "demo-supervisor")
    b = customer_trials.create_trial(s, request(), "demo-supervisor")
    assert planning_snapshot(s) == fleet_before
    from fleet_maintenance.api.routes.scenarios import scenarios

    scenario_ids = {item["id"] for item in scenarios(s)}
    assert a.id not in scenario_ids and b.id not in scenario_ids
    assert a.baseline_scenario_id in scenario_ids
    for trial in (a, b):
        evidence = add_assessment(s, trial)
        snapshot = customer_trials.trial_planning_snapshot(s, trial.id)
        assert snapshot["advisory"]["assessment_id"] == evidence.id
        assert snapshot["advisory"]["effective_deadline_hours"] == 80
        source = restore_source(snapshot)
        assert set(source.part_stock) == {trial.part_id}
        assert {task.id for task in source.tasks} == {f"{trial.id}-task"}
        plan = propose_plan(s, snapshot=snapshot)
        assert plan.assignments[0]["start"] == 0
        approve_plan(s, plan.id, "demo-supervisor")
        assert approve_plan(s, plan.id, "demo-supervisor").id == plan.id
        history = plan_commitment(s, plan.id)
        work = history["work"][0]
        started = update_work(
            s, work["id"], "start", work["version"], "demo-supervisor", "Test start"
        )
        completed = update_work(
            s, started.id, "complete", started.version, "demo-supervisor", "Test complete"
        )
        assert completed.consumed_quantity == 1
        assert s.get(Part, trial.part_id).on_hand == 0
    assert planning_snapshot(s) == fleet_before


def test_expected_stock_cannot_approve_and_receipt_invalidates_proposal(
    isolated_session, trial_catalog
):
    s = isolated_session
    trial = customer_trials.create_trial(s, request(spare_on_hand=0), "demo-supervisor")
    add_assessment(s, trial)
    plan = propose_plan(s, snapshot=customer_trials.trial_planning_snapshot(s, trial.id))
    assert plan.assignments[0]["start"] == 3
    with pytest.raises(ApprovalConflict, match="Awaiting received stock"):
        approve_plan(s, plan.id, "demo-supervisor")
    s.rollback()
    record_arrival(s, trial.arrival_id, "receive", 1, "Test delivery", "demo-supervisor")
    with pytest.raises(ApprovalConflict, match="inputs changed"):
        approve_plan(s, plan.id, "demo-supervisor")
    s.rollback()
    new = propose_plan(s, snapshot=customer_trials.trial_planning_snapshot(s, trial.id))
    assert new.assignments[0]["start"] == 0
    approve_plan(s, new.id, "demo-supervisor")
    assert s.get(Part, trial.part_id).on_hand == 0


def test_window_uses_units_rounds_down_and_never_relaxes_mandatory_deadline(
    isolated_session, trial_catalog
):
    s = isolated_session
    trial = customer_trials.create_trial(s, request(deadline_slot=3), "demo-supervisor")
    add_assessment(s, trial, lower=40.0)
    snapshot = customer_trials.trial_planning_snapshot(s, trial.id)
    assert snapshot["advisory"]["effective_deadline_hours"] == 24
    another = customer_trials.create_trial(s, request(cycles_per_day=120.0), "demo-supervisor")
    add_assessment(s, another, lower=1.0)
    blocked = propose_plan(s, snapshot=customer_trials.trial_planning_snapshot(s, another.id))
    assert blocked.status == "invalid"
    assert not blocked.assignments
    with pytest.raises(ApprovalConflict):
        approve_plan(s, blocked.id, "demo-supervisor")


def test_requires_matching_available_evidence_and_rejects_unknown_scope(
    isolated_session, trial_catalog
):
    s = isolated_session
    trial = customer_trials.create_trial(s, request(), "demo-supervisor")
    with pytest.raises(ApprovalConflict, match="matching available"):
        customer_trials.trial_planning_snapshot(s, trial.id)
    add_assessment(s, trial, state="unavailable")
    with pytest.raises(ApprovalConflict, match="matching available"):
        customer_trials.trial_planning_snapshot(s, trial.id)
    with pytest.raises(ValueError, match="Unknown customer trial"):
        planning_snapshot(s, "cmp-eng-01")


def test_replay_conflict_and_failed_trial_are_atomic(isolated_session, trial_catalog):
    s = isolated_session
    body = request()
    first = customer_trials.create_trial(s, body, "demo-supervisor")
    assert customer_trials.create_trial(s, body, "demo-supervisor") == first
    with pytest.raises(ApprovalConflict, match="different inputs"):
        customer_trials.create_trial(
            s, body.model_copy(update={"spare_on_hand": 2}), "demo-supervisor"
        )
    bad = request(duration_slots=4, deadline_slot=1)
    with pytest.raises(ValueError, match="cannot fit"):
        customer_trials.create_trial(s, bad, "demo-supervisor")
    assert s.get(Aircraft, bad.id) is None
    assert list(s.scalars(select(Part).where(Part.id == f"{bad.id}-kit"))) == []


def test_corrected_history_blocks_old_trial_approval(isolated_session, trial_catalog):
    from fleet_maintenance.persistence.models import ImportRecord
    from fleet_maintenance.services.imports import import_history

    s = isolated_session
    trial = customer_trials.create_trial(s, request(), "demo-supervisor")
    add_assessment(s, trial)
    plan = propose_plan(s, snapshot=customer_trials.trial_planning_snapshot(s, trial.id))
    original = s.get(ImportRecord, trial.import_id)
    rows = [dict(row) for row in original.rows]
    rows[-1] = {"cycle": 40, "values": [2.0] * 24}
    import_history(
        s,
        trial.component_id,
        "corrected-test",
        trial.engine_identity,
        rows,
        trial.import_id,
        "demo-supervisor",
    )
    with pytest.raises(ApprovalConflict, match="history changed"):
        approve_plan(s, plan.id, "demo-supervisor")
    assert s.get(Part, trial.part_id).on_hand == 1


def test_customer_routes_are_unavailable_outside_local_demo(monkeypatch):
    from types import SimpleNamespace

    from fastapi import HTTPException

    from fleet_maintenance.api.routes import demo

    for environment, authentication in (("production", "session"), ("development", "session")):
        monkeypatch.setattr(
            demo,
            "get_settings",
            lambda env=environment, auth=authentication: SimpleNamespace(
                environment=env, authentication_mode=auth
            ),
        )
        with pytest.raises(HTTPException) as exc:
            demo.local_demo()
        assert exc.value.status_code == 403
