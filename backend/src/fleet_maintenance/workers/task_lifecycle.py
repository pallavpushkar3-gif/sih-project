TERMINAL = {"succeeded", "failed", "cancelled"}
ALLOWED = {
    "queued": {"running", "cancelled"},
    "running": {"succeeded", "failed", "cancellation_requested"},
    "cancellation_requested": {"cancelled", "failed"},
}


def transition(current: str, target: str) -> str:
    if current in TERMINAL:
        raise ValueError("Terminal jobs cannot transition.")
    if target not in ALLOWED.get(current, set()):
        raise ValueError(f"Invalid transition: {current} -> {target}")
    return target
