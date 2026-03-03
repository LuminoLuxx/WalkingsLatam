from __future__ import annotations

from datetime import datetime
from typing import Dict, List

STAGE_ORDER = [
    "Recepción",
    "Pre-assessment",
    "Testing",
    "Waiting room post-testing",
    "Decisión final",
    "Compliance",
    "Contratado",
    "No contratado",
    "Abandonó",
]

TERMINAL_STAGES = {"Contratado", "No contratado", "Abandonó"}

ROLE_BY_STAGE = {
    "Recepción": "Recepción",
    "Pre-assessment": "Reclutador",
    "Testing": "Testing POC",
    "Waiting room post-testing": "Reclutador",
    "Decisión final": "Reclutador",
    "Compliance": "Compliance",
    "Contratado": "Compliance",
    "No contratado": "Reclutador",
    "Abandonó": "Recepción",
}

TRANSITIONS: Dict[str, List[str]] = {
    "Recepción": ["Pre-assessment", "Abandonó"],
    "Pre-assessment": ["Testing", "No contratado", "Abandonó"],
    "Testing": ["Waiting room post-testing", "Abandonó"],
    "Waiting room post-testing": ["Decisión final", "Abandonó"],
    "Decisión final": ["Compliance", "No contratado", "Abandonó"],
    "Compliance": ["Contratado", "No contratado", "Abandonó"],
    "Contratado": [],
    "No contratado": [],
    "Abandonó": [],
}

TIMESTAMP_COLUMNS = {
    "Recepción": "ts_recepcion",
    "Pre-assessment": "ts_preassessment_start",
    "Testing": "ts_testing_start",
    "Waiting room post-testing": "ts_testing_end",
    "Decisión final": "ts_decision_start",
    "Compliance": "ts_compliance_start",
    "Contratado": "ts_closed",
    "No contratado": "ts_closed",
    "Abandonó": "ts_abandono",
}


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def can_transition(current_stage: str, new_stage: str) -> bool:
    return new_stage in TRANSITIONS.get(current_stage, [])


def move_ticket_record(record: dict, new_stage: str, abandon_reason: str = "") -> dict:
    current = record["status"]
    if not can_transition(current, new_stage):
        raise ValueError("Transición no válida")

    ts = now_iso()
    record = record.copy()
    record["status"] = new_stage
    record["current_owner"] = ROLE_BY_STAGE[new_stage]
    record["updated_at"] = ts
    record[TIMESTAMP_COLUMNS[new_stage]] = ts
    if new_stage == "Abandonó":
        record["abandon_reason"] = abandon_reason
    return record
