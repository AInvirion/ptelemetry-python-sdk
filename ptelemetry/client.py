# ProductTelemetry Python SDK
# Copyright (c) 2025-2026 AInvirion LLC. All Rights Reserved.

from __future__ import annotations

import atexit
import json
import logging
import os
import re
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx

logger = logging.getLogger("producttelemetry")

EventType = Literal["lifecycle", "usage", "error"]

# Default API endpoint
DEFAULT_API_URL = "https://producttelemetry.com/api"


class Telemetry:
    """
    ProductTelemetry client.

    Usage:
        from producttelemetry import Telemetry

        t = Telemetry(write_key="proj_wk_xxx")
        t.track("cli.started", event_type="lifecycle")
        t.track("command.executed", {"command": "export"})
        t.identify(user_id="usr_123")
    """

    def __init__(
        self,
        write_key: str | None = None,
        api_url: str | None = None,
        disabled: bool = False,
        flush_interval: float = 30.0,
        flush_at: int = 10,
        max_queue_size: int = 1000,
        project_slug: str = "default",
    ):
        """
        Initialize the telemetry client.

        Args:
            write_key: Project write key (or set OPS_WRITE_KEY env var)
            api_url: API endpoint URL (default: https://api.openproductstats.com)
            disabled: Disable all telemetry (or set DO_NOT_TRACK=1 / OPS_TELEMETRY=0)
            flush_interval: Seconds between automatic flushes (default: 30)
            flush_at: Number of events to trigger a flush (default: 10)
            max_queue_size: Maximum events to queue before dropping (default: 1000)
            project_slug: Project slug for client_id isolation (default: "default")
        """
        self._write_key = write_key or os.environ.get("OPS_WRITE_KEY", "")
        self._api_url = (api_url or os.environ.get("OPS_API_URL", DEFAULT_API_URL)).rstrip("/")
        # Sanitize project_slug to prevent path traversal
        if not re.match(r"^[a-zA-Z0-9_-]+$", project_slug):
            raise ValueError(
                f"Invalid project_slug '{project_slug}': must contain only alphanumeric, dash, or underscore"
            )
        self._project_slug = project_slug
        self._flush_interval = flush_interval
        self._flush_at = flush_at
        self._max_queue_size = max_queue_size

        # Check opt-out mechanisms
        self._disabled = disabled or self._check_opt_out()

        # Event queue
        self._queue: list[dict] = []
        self._queue_lock = threading.Lock()

        # Client ID (lazily loaded)
        self._client_id: str | None = None

        # Background flush timer
        self._timer: threading.Timer | None = None
        self._shutdown = False

        # Load any persisted offline events
        if not self._disabled and self._write_key:
            self._load_pending_events()
            self._start_flush_timer()
            atexit.register(self._shutdown_handler)

    def _check_opt_out(self) -> bool:
        """Check all opt-out mechanisms."""
        # Environment variables
        if os.environ.get("DO_NOT_TRACK") == "1":
            return True
        if os.environ.get("OPS_TELEMETRY") == "0":
            return True

        # Config file check
        config_path = self._get_config_dir() / "config.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
                if config.get("telemetry") is False:
                    return True
            except Exception as e:
                # Fail closed: if user has a config file but it's unreadable/malformed,
                # assume they intended to opt out (privacy-first)
                logger.warning("Failed to parse opt-out config, disabling telemetry: %s", e)
                return True

        return False

    def _get_config_dir(self) -> Path:
        """Get the config directory for this project."""
        base = Path.home() / ".config" / "producttelemetry" / self._project_slug
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _get_client_id(self) -> str:
        """Get or create a persistent client ID."""
        if self._client_id:
            return self._client_id

        client_id_path = self._get_config_dir() / "client_id"

        if client_id_path.exists():
            self._client_id = client_id_path.read_text().strip()
        else:
            self._client_id = str(uuid.uuid4())
            client_id_path.write_text(self._client_id)

        return self._client_id

    def _get_pending_events_path(self) -> Path:
        """Get the path for persisted offline events."""
        return self._get_config_dir() / "pending_events.json"

    def _load_pending_events(self) -> None:
        """Load any persisted events from disk into the queue."""
        pending_path = self._get_pending_events_path()
        if not pending_path.exists():
            return

        try:
            data = json.loads(pending_path.read_text())
            events = data.get("events", [])
            if events:
                with self._queue_lock:
                    # Merge with any existing queue, keeping most recent up to max
                    combined = self._queue + events
                    if len(combined) > self._max_queue_size:
                        # Keep most recent events (they're at the end)
                        combined = combined[-self._max_queue_size:]
                    self._queue = combined
                logger.debug("Loaded %d pending events from disk", len(events))
            # Clear the file after loading
            pending_path.unlink()
        except Exception as e:
            logger.debug("Failed to load pending events: %s", e)

    def _persist_events(self, events: list[dict]) -> None:
        """Persist events to disk for offline storage."""
        if not events:
            return

        pending_path = self._get_pending_events_path()

        try:
            # Load existing persisted events
            existing: list[dict] = []
            if pending_path.exists():
                try:
                    data = json.loads(pending_path.read_text())
                    existing = data.get("events", [])
                except Exception:
                    pass

            # Combine and trim to max size (keep most recent)
            combined = existing + events
            if len(combined) > self._max_queue_size:
                combined = combined[-self._max_queue_size:]

            # Write to disk
            pending_path.write_text(json.dumps({"events": combined}, default=str))
            logger.debug("Persisted %d events to disk (total: %d)", len(events), len(combined))
        except Exception as e:
            logger.debug("Failed to persist events: %s", e)

    def _shutdown_handler(self) -> None:
        """Handle shutdown: try to flush, persist remaining events."""
        self._shutdown = True
        if self._timer:
            self._timer.cancel()

        # Try to flush
        with self._queue_lock:
            if not self._queue:
                return
            events = self._queue.copy()
            self._queue.clear()

        if not events:
            return

        # Attempt to send
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{self._api_url}/ingest",
                    json={"events": events},
                    headers={"X-Write-Key": self._write_key},
                )
                if response.status_code in (200, 207):
                    return  # Success, events sent
        except Exception:
            pass

        # Failed to send, persist to disk
        self._persist_events(events)

    def _start_flush_timer(self) -> None:
        """Start the background flush timer."""
        if self._shutdown:
            return
        self._timer = threading.Timer(self._flush_interval, self._timer_flush)
        self._timer.daemon = True
        self._timer.start()

    def _timer_flush(self) -> None:
        """Called by the timer to flush and restart."""
        self.flush()
        self._start_flush_timer()

    def track(
        self,
        event_name: str,
        properties: dict[str, Any] | None = None,
        event_type: EventType = "usage",
        timestamp: datetime | None = None,
    ) -> None:
        """
        Track an event.

        Args:
            event_name: Name of the event (e.g., "cli.command.executed")
            properties: Optional event properties
            event_type: Type of event ("lifecycle", "usage", or "error")
            timestamp: Event timestamp (default: now)
        """
        if self._disabled or not self._write_key:
            return

        event = {
            "event_name": event_name,
            "event_type": event_type,
            "client_id": self._get_client_id(),
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "properties": properties or {},
        }

        with self._queue_lock:
            if len(self._queue) < self._max_queue_size:
                self._queue.append(event)

                if len(self._queue) >= self._flush_at:
                    # Flush in background thread
                    threading.Thread(target=self.flush, daemon=True).start()

    def error(
        self,
        exception: Exception | None = None,
        message: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """
        Track an error event.

        Args:
            exception: Exception object to capture
            message: Error message (if no exception provided)
            properties: Additional properties
        """
        props = properties.copy() if properties else {}

        if exception:
            props["error_type"] = type(exception).__name__
            props["error_message"] = str(exception)
            props["stack_trace"] = "".join(
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            )
        elif message:
            props["error_message"] = message

        event_name = f"error.{props.get('error_type', 'unknown')}"
        self.track(event_name, props, event_type="error")

    def identify(self, user_id: str) -> None:
        """
        Link this client to a known user ID.

        Args:
            user_id: Your application's user identifier
        """
        if self._disabled or not self._write_key:
            return

        try:
            with httpx.Client(timeout=10.0) as client:
                client.post(
                    f"{self._api_url}/identify",
                    json={
                        "client_id": self._get_client_id(),
                        "user_id": user_id,
                    },
                    headers={"X-Write-Key": self._write_key},
                )
        except Exception as e:
            logger.debug("Failed to identify user: %s", e)

    def request_deletion(self) -> bool:
        """
        Request deletion of all data for this client (GDPR).

        Returns:
            True if request was submitted successfully
        """
        if not self._write_key:
            return False

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.request(
                    "DELETE",
                    f"{self._api_url}/gdpr/delete-self",
                    json={"client_id": self._get_client_id()},
                    headers={"X-Write-Key": self._write_key},
                )
                if response.status_code in (200, 202):
                    # Clear local client ID
                    client_id_path = self._get_config_dir() / "client_id"
                    if client_id_path.exists():
                        client_id_path.unlink()
                    self._client_id = None
                    return True
        except Exception as e:
            logger.debug("Failed to request deletion: %s", e)

        return False

    def flush(self) -> None:
        """Flush all queued events to the server."""
        if self._disabled or not self._write_key:
            return

        with self._queue_lock:
            if not self._queue:
                return
            events = self._queue.copy()
            self._queue.clear()

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self._api_url}/ingest",
                    json={"events": events},
                    headers={"X-Write-Key": self._write_key},
                )
                if response.status_code not in (200, 207):
                    # Server error - persist to disk for later retry
                    self._persist_events(events)
        except Exception as e:
            logger.debug("Failed to flush events (offline?): %s", e)
            # Network failure - persist to disk for later retry
            self._persist_events(events)

    def shutdown(self) -> None:
        """Shutdown the client, flushing remaining events."""
        self._shutdown_handler()

    def __enter__(self) -> Telemetry:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
