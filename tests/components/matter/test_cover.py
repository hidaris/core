"""Test Matter locks."""
from unittest.mock import MagicMock, call

from chip.clusters import Objects as clusters
from matter_server.client.models.node import MatterNode
import pytest

from homeassistant.components.cover import (
    STATE_OPEN,
    STATE_OPENING,
    STATE_CLOSING,
    STATE_CLOSED,
)
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from .common import (
    set_node_attribute,
    setup_integration_with_node_fixture,
    trigger_subscription_callback,
)


@pytest.fixture(name="window_covering")
async def door_lock_fixture(
    hass: HomeAssistant, matter_client: MagicMock
) -> MatterNode:
    """Fixture for a window covering node."""
    return await setup_integration_with_node_fixture(
        hass, "window-covering", matter_client
    )


# This tests needs to be adjusted to remove lingering tasks
@pytest.mark.parametrize("expected_lingering_tasks", [True])
async def test_lock(
    hass: HomeAssistant,
    matter_client: MagicMock,
    window_covering: MatterNode,
) -> None:
    """Test window covering."""
    await hass.services.async_call(
        "cover",
        "close_cover",
        {
            "entity_id": "cover.mock_window_covering",
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=window_covering.node_id,
        endpoint_id=1,
        command=clusters.WindowCovering.Commands.DownOrClose(),
        timed_request_timeout_ms=1000,
    )
    matter_client.send_device_command.reset_mock()

    await hass.services.async_call(
        "cover",
        "stop_cover",
        {
            "entity_id": "cover.mock_window_covering",
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=window_covering.node_id,
        endpoint_id=1,
        command=clusters.WindowCovering.Commands.StopMotion(),
        timed_request_timeout_ms=1000,
    )
    matter_client.send_device_command.reset_mock()

    await hass.services.async_call(
        "cover",
        "open_cover",
        {
            "entity_id": "cover.mock_window_covering",
        },
        blocking=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=window_covering.node_id,
        endpoint_id=1,
        command=clusters.WindowCovering.Commands.UpOrOpen(),
        timed_request_timeout_ms=1000,
    )
    matter_client.send_device_command.reset_mock()

    state = hass.states.get("cover.mock_window_covering")
    assert state
    assert state.state == STATE_OPEN

    set_node_attribute(window_covering, 1, 258, 8, 50)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("cover.mock_window_covering")
    assert state
    assert state.state == STATE_CLOSING

    set_node_attribute(window_covering, 1, 258, 8, 0)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("cover.mock_window_covering")
    assert state
    assert state.state == STATE_CLOSED

    set_node_attribute(window_covering, 1, 258, 8, 50)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("cover.mock_window_covering")
    assert state
    assert state.state == STATE_OPENING

    set_node_attribute(window_covering, 1, 258, 8, None)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("cover.mock_window_covering")
    assert state
    assert state.state == STATE_UNKNOWN
