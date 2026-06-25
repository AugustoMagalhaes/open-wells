import socket
from unittest.mock import patch

from omni_wells.app import _find_free_port


def test_find_free_port_returns_5000_when_available():
    port = _find_free_port(start=5000)
    assert isinstance(port, int)
    assert port >= 5000


def test_find_free_port_skips_occupied_port():
    with socket.socket() as s:
        s.bind(("", 0))
        occupied = s.getsockname()[1]
        port = _find_free_port(start=occupied)
        assert port != occupied
        assert port > occupied


def test_find_free_port_increments_until_free():
    call_count = 0

    original_socket = socket.socket

    class MockSocket:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def bind(self, addr):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("port in use")

        def getsockname(self):
            return ("", 5002)

    with patch("omni_wells.app.socket.socket", MockSocket):
        port = _find_free_port(start=5000)
        assert port == 5002
        assert call_count == 3
