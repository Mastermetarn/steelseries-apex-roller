"""Sonar mute endpoints: URL shape per mode and JSON parsing."""
from __future__ import annotations

import pytest

from apex_roller import sonar as sonar_mod
from apex_roller.sonar import Sonar, SonarError

VOLUMES = {
    "masters": {
        "stream": {"streaming": {"volume": 0.7, "muted": False},
                   "monitoring": {"volume": 0.3, "muted": True}},
        "classic": {"volume": 0.9, "muted": True},
    },
    "devices": {
        "game": {
            "stream": {"streaming": {"volume": 0.1, "muted": True},
                       "monitoring": {"volume": 0.2, "muted": False}},
            "classic": {"volume": 0.4, "muted": False},
        },
    },
}


class FakeResponse:
    def __init__(self, payload=None):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def client(monkeypatch):
    puts: list[str] = []
    monkeypatch.setattr(sonar_mod.requests, "get", lambda url, timeout: FakeResponse(VOLUMES))
    monkeypatch.setattr(sonar_mod.requests, "put",
                        lambda url, timeout: (puts.append(url), FakeResponse())[1])
    s = Sonar.__new__(Sonar)
    s.timeout = 1.0
    s.base_url = "http://sonar"
    s.mode = "stream"
    s.puts = puts
    return s


def test_get_muted_streamer(client):
    assert client.get_muted("game", "streaming") is True
    assert client.get_muted("game", "monitoring") is False
    assert client.get_muted("master", "monitoring") is True


def test_get_muted_classic(client):
    client.mode = "classic"
    assert client.get_muted("master") is True
    assert client.get_muted("game") is False


def test_set_muted_streamer_url(client):
    client.set_muted("game", True, "monitoring")
    assert client.puts == ["http://sonar/volumeSettings/streamer/monitoring/game/isMuted/true"]


def test_set_muted_classic_url(client):
    client.mode = "classic"
    client.set_muted("game", False)
    assert client.puts == ["http://sonar/volumeSettings/classic/game/Mute/false"]


def test_set_muted_streamer_requires_slider(client):
    with pytest.raises(SonarError):
        client._set_muted("game", True, None)
