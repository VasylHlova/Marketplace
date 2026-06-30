import pytest


@pytest.mark.asyncio
async def test_websocket_connect_disconnect(manager, mocker):
    ws1 = mocker.AsyncMock()
    ws2 = mocker.AsyncMock()
    await manager.connect(ws1, "room_1", "user_1")
    ws1.accept.assert_called_once()
    assert "room_1" in manager.active_connections
    assert "user_1" in manager.active_connections["room_1"]
    assert ws1 in manager.active_connections["room_1"]["user_1"]
    await manager.connect(ws2, "room_1", "user_2")
    await manager.broadcast_to_room("room_1", {"msg": "hello"})
    ws1.send_json.assert_called_once_with({"msg": "hello"})
    ws2.send_json.assert_called_once_with({"msg": "hello"})
    manager.disconnect(ws1, "room_1", "user_1")
    assert "user_1" not in manager.active_connections["room_1"]
    assert "user_2" in manager.active_connections["room_1"]
    manager.disconnect(ws2, "room_1", "user_2")
    assert "room_1" not in manager.active_connections
