from workflow import ROLE_BY_STAGE, can_transition, move_ticket_record


def base_record():
    return {
        "ticket_id": "GT-WALK-0001",
        "status": "Recepción",
        "current_owner": "Recepción",
        "updated_at": "2026-01-01 10:00:00",
        "ts_recepcion": "2026-01-01 10:00:00",
        "ts_preassessment_start": "",
        "ts_testing_start": "",
        "ts_testing_end": "",
        "ts_decision_start": "",
        "ts_compliance_start": "",
        "ts_closed": "",
        "ts_abandono": "",
        "abandon_reason": "",
    }


def test_move_ticket_updates_owner_and_timestamp():
    result = move_ticket_record(base_record(), "Pre-assessment")
    assert result["status"] == "Pre-assessment"
    assert result["current_owner"] == ROLE_BY_STAGE["Pre-assessment"]
    assert result["ts_preassessment_start"] != ""


def test_transition_matrix():
    assert can_transition("Recepción", "Pre-assessment")
    assert not can_transition("Recepción", "Compliance")
