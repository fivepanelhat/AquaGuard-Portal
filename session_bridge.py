"""Soft SessionEvent + Trajectory for portal plan cycles (Core ≥0.5.9)."""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from coastal_alpine_core import SessionEventStore, record_session_trajectory
except ImportError:  # pragma: no cover
    SessionEventStore = None  # type: ignore
    record_session_trajectory = None  # type: ignore


class PortalSession:
    """Null-safe session audit for edge plan cycles."""

    def __init__(self, portal_name: str, tenant_id: str = "default"):
        self.portal_name = portal_name
        self.tenant_id = tenant_id
        self.store = None
        if SessionEventStore is not None:
            try:
                self.store = SessionEventStore(
                    storage_path=f"session_events_{portal_name}.jsonl"
                )
            except Exception as exc:
                logger.debug("SessionEventStore init failed: %s", exc)

    def new_session_id(self) -> str:
        return str(uuid.uuid4())

    def emit(
        self,
        session_id: str,
        event_type: str,
        *,
        actor: str = "portal",
        payload: Optional[dict] = None,
        outcome: Optional[str] = None,
    ) -> None:
        if self.store is None:
            return
        try:
            self.store.emit(
                session_id=session_id,
                event_type=event_type,
                actor=actor,
                tenant_id=self.tenant_id,
                payload=payload or {},
                outcome=outcome,
            )
        except Exception as exc:
            logger.debug("session emit failed: %s", exc)

    def complete_cycle(
        self,
        session_id: str,
        *,
        action: str,
        outcome: str,
        latency_seconds: float,
        input_summary: str = "",
        output_summary: str = "",
        flywheel_path: str | None = None,
    ) -> None:
        self.emit(
            session_id,
            "session_end",
            payload={"action": action},
            outcome=outcome,
        )
        if record_session_trajectory is None:
            return
        try:
            kwargs: dict[str, Any] = dict(
                session_id=session_id,
                action=action,
                outcome=outcome,
                input_summary=input_summary,
                output_summary=output_summary,
                latency_seconds=latency_seconds,
                tenant_id=self.tenant_id,
            )
            if flywheel_path:
                kwargs["storage_path"] = flywheel_path
            record_session_trajectory(**kwargs)
        except Exception as exc:
            logger.debug("trajectory failed: %s", exc)


def timed() -> float:
    return time.perf_counter()
