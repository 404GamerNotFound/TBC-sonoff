import asyncio
import json
from pathlib import Path

from sonoff.module import SonoffCameraModule
from tbc_camera_api import CameraCapability

_PLUGIN_DIR = Path(__file__).resolve().parent.parent


def _manifest() -> dict:
    return json.loads((_PLUGIN_DIR / "manifest.json").read_text(encoding="utf-8"))


def test_manifest_capabilities_match_module_class():
    manifest = _manifest()
    manifest_capabilities = {CameraCapability(value) for value in manifest["capabilities"]}
    assert manifest_capabilities == SonoffCameraModule.capabilities
    assert manifest_capabilities == {CameraCapability.LIVE}


def test_manifest_key_and_ports_match_manual_rtsp_defaults():
    manifest = _manifest()
    module = SonoffCameraModule()
    assert manifest["key"] == "sonoff"
    assert module.requires_manual_stream_uri is True
    assert module.requires_credentials is False


def test_probe_rejects_invalid_manual_stream_uri():
    module = SonoffCameraModule()
    snapshot = asyncio.run(module.probe({"manual_stream_uri": "not-a-valid-uri"}))
    assert snapshot.status == "error"
    assert "eWeLink" in snapshot.message


def test_probe_accepts_rtsp_uri_shape(monkeypatch):
    from tbc_camera_api import streams as manual_rtsp_streams

    monkeypatch.setattr(
        manual_rtsp_streams, "probe_rtsp_stream", lambda uri, **kwargs: ("ok", "RTSP-Stream erreichbar")
    )
    module = SonoffCameraModule()
    snapshot = asyncio.run(module.probe({"manual_stream_uri": "rtsp://example.invalid:554/live/stream"}))
    assert snapshot.status == "ok"
    assert snapshot.stream_uri == "rtsp://example.invalid:554/live/stream"
