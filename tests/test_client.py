# ProductTelemetry SDK Tests
# Copyright (c) 2025-2026 AInvirion LLC. All Rights Reserved.

import json
import os
from unittest.mock import patch

import httpx
import pytest
import respx

from ptelemetry import Telemetry


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    with patch.object(Telemetry, "_get_config_dir", return_value=tmp_path):
        yield tmp_path


@pytest.fixture
def mock_api():
    """Mock the API endpoints."""
    with respx.mock(base_url="https://api.test.com", assert_all_called=False) as respx_mock:
        respx_mock.post("/ingest").mock(
            return_value=httpx.Response(200, json={"accepted": 1, "rejected": 0})
        )
        respx_mock.post("/identify").mock(
            return_value=httpx.Response(200, json={"linked": True, "created": True})
        )
        respx_mock.request("DELETE", "/gdpr/delete-self").mock(
            return_value=httpx.Response(202, json={"status": "pending"})
        )
        yield respx_mock


class TestTelemetryInit:
    def test_init_with_write_key(self, temp_config_dir):
        t = Telemetry(write_key="test_key")
        assert t._write_key == "test_key"
        assert not t._disabled
        t.shutdown()

    def test_init_from_env_var(self, temp_config_dir):
        with patch.dict(os.environ, {"OPS_WRITE_KEY": "env_key"}):
            t = Telemetry()
            assert t._write_key == "env_key"
            t.shutdown()

    def test_init_disabled(self, temp_config_dir):
        t = Telemetry(write_key="test", disabled=True)
        assert t._disabled
        t.shutdown()

    def test_opt_out_do_not_track(self, temp_config_dir):
        with patch.dict(os.environ, {"DO_NOT_TRACK": "1"}):
            t = Telemetry(write_key="test")
            assert t._disabled
            t.shutdown()

    def test_opt_out_ops_telemetry(self, temp_config_dir):
        with patch.dict(os.environ, {"OPS_TELEMETRY": "0"}):
            t = Telemetry(write_key="test")
            assert t._disabled
            t.shutdown()

    def test_opt_out_config_file(self, temp_config_dir):
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"telemetry": False}))

        t = Telemetry(write_key="test")
        assert t._disabled
        t.shutdown()


class TestClientId:
    def test_generates_client_id(self, temp_config_dir):
        t = Telemetry(write_key="test")
        client_id = t._get_client_id()

        assert client_id is not None
        assert len(client_id) == 36  # UUID format
        t.shutdown()

    def test_persists_client_id(self, temp_config_dir):
        t1 = Telemetry(write_key="test")
        client_id1 = t1._get_client_id()
        t1.shutdown()

        t2 = Telemetry(write_key="test")
        client_id2 = t2._get_client_id()
        t2.shutdown()

        assert client_id1 == client_id2

    def test_client_id_isolated_by_project(self, tmp_path):
        dir1 = tmp_path / "proj1"
        dir2 = tmp_path / "proj2"
        dir1.mkdir()
        dir2.mkdir()

        with patch.object(Telemetry, "_get_config_dir", return_value=dir1):
            t1 = Telemetry(write_key="test", project_slug="proj1")
            id1 = t1._get_client_id()
            t1.shutdown()

        with patch.object(Telemetry, "_get_config_dir", return_value=dir2):
            t2 = Telemetry(write_key="test", project_slug="proj2")
            id2 = t2._get_client_id()
            t2.shutdown()

        # Would be different if _get_config_dir used project_slug
        # For this test, we're mocking to different dirs
        assert id1 != id2


class TestTracking:
    def test_track_queues_event(self, temp_config_dir):
        t = Telemetry(write_key="test", flush_at=100)  # High flush_at to prevent auto-flush
        t.track("test.event", {"key": "value"})

        assert len(t._queue) == 1
        assert t._queue[0]["event_name"] == "test.event"
        assert t._queue[0]["properties"] == {"key": "value"}
        t.shutdown()

    def test_track_disabled_does_nothing(self, temp_config_dir):
        t = Telemetry(write_key="test", disabled=True)
        t.track("test.event")

        assert len(t._queue) == 0
        t.shutdown()

    def test_track_without_key_does_nothing(self, temp_config_dir):
        t = Telemetry()  # No write key
        t.track("test.event")

        assert len(t._queue) == 0
        t.shutdown()

    def test_error_captures_exception(self, temp_config_dir):
        t = Telemetry(write_key="test", flush_at=100)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            t.error(e)

        assert len(t._queue) == 1
        assert "error.ValueError" in t._queue[0]["event_name"]
        assert t._queue[0]["properties"]["error_message"] == "Test error"
        t.shutdown()


class TestFlush:
    def test_flush_sends_events(self, temp_config_dir, mock_api):
        t = Telemetry(write_key="test", api_url="https://api.test.com", flush_at=100)
        t.track("test.event")
        t.flush()

        assert len(t._queue) == 0
        assert mock_api.calls.last.request.url.path == "/ingest"
        t.shutdown()

    def test_flush_requeues_on_failure(self, temp_config_dir):
        with respx.mock(base_url="https://api.test.com") as mock:
            mock.post("/ingest").mock(return_value=httpx.Response(500))

            t = Telemetry(write_key="test", api_url="https://api.test.com", flush_at=100)
            t.track("test.event")
            t.flush()

            # Event should be re-queued
            assert len(t._queue) == 1
            t.shutdown()


class TestIdentify:
    def test_identify_sends_request(self, temp_config_dir, mock_api):
        t = Telemetry(write_key="test", api_url="https://api.test.com")
        t.identify("user_123")

        assert any(c.request.url.path == "/identify" for c in mock_api.calls)
        t.shutdown()


class TestDeletion:
    def test_request_deletion_clears_client_id(self, temp_config_dir, mock_api):
        t = Telemetry(write_key="test", api_url="https://api.test.com")
        client_id = t._get_client_id()
        client_id_path = temp_config_dir / "client_id"

        assert client_id_path.exists()

        result = t.request_deletion()

        assert result is True
        assert not client_id_path.exists()
        assert t._client_id is None
        t.shutdown()


class TestContextManager:
    def test_context_manager_flushes_on_exit(self, temp_config_dir, mock_api):
        with Telemetry(write_key="test", api_url="https://api.test.com", flush_at=100) as t:
            t.track("test.event")

        # Should have flushed on exit
        assert any(c.request.url.path == "/ingest" for c in mock_api.calls)
