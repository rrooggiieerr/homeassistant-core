"""The tests for the Ring switch platform."""

from unittest.mock import Mock

import pytest
import ring_doorbell
from syrupy.assertion import SnapshotAssertion

from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .common import MockConfigEntry, setup_platform

from tests.common import snapshot_platform


async def test_entity_registry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_ring_client,
) -> None:
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(hass, Platform.SWITCH)

    entry = entity_registry.async_get("switch.front_siren")
    assert entry.unique_id == "765432-siren"

    entry = entity_registry.async_get("switch.internal_siren")
    assert entry.unique_id == "345678-siren"


async def test_states(
    hass: HomeAssistant,
    mock_ring_client: Mock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test states."""

    mock_config_entry.add_to_hass(hass)
    await setup_platform(hass, Platform.SWITCH)
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


async def test_siren_off_reports_correctly(
    hass: HomeAssistant, mock_ring_client
) -> None:
    """Tests that the initial state of a device that should be off is correct."""
    await setup_platform(hass, Platform.SWITCH)

    state = hass.states.get("switch.front_siren")
    assert state.state == "off"
    assert state.attributes.get("friendly_name") == "Front Siren"


async def test_siren_on_reports_correctly(
    hass: HomeAssistant, mock_ring_client
) -> None:
    """Tests that the initial state of a device that should be on is correct."""
    await setup_platform(hass, Platform.SWITCH)

    state = hass.states.get("switch.internal_siren")
    assert state.state == "on"
    assert state.attributes.get("friendly_name") == "Internal Siren"


async def test_siren_can_be_turned_on(hass: HomeAssistant, mock_ring_client) -> None:
    """Tests the siren turns on correctly."""
    await setup_platform(hass, Platform.SWITCH)

    state = hass.states.get("switch.front_siren")
    assert state.state == "off"

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.front_siren"}, blocking=True
    )

    await hass.async_block_till_done()
    state = hass.states.get("switch.front_siren")
    assert state.state == "on"


@pytest.mark.parametrize(
    ("exception_type", "reauth_expected"),
    [
        (ring_doorbell.AuthenticationError, True),
        (ring_doorbell.RingTimeout, False),
        (ring_doorbell.RingError, False),
    ],
    ids=["Authentication", "Timeout", "Other"],
)
async def test_switch_errors_when_turned_on(
    hass: HomeAssistant,
    mock_ring_client,
    mock_ring_devices,
    exception_type,
    reauth_expected,
) -> None:
    """Tests the switch turns on correctly."""
    await setup_platform(hass, Platform.SWITCH)
    config_entry = hass.config_entries.async_entries("ring")[0]

    assert not any(config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))

    front_siren_mock = mock_ring_devices.get_device(765432)
    front_siren_mock.async_set_siren.side_effect = exception_type

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": "switch.front_siren"}, blocking=True
        )
    await hass.async_block_till_done()
    front_siren_mock.async_set_siren.assert_called_once()
    assert (
        any(
            flow
            for flow in config_entry.async_get_active_flows(hass, {SOURCE_REAUTH})
            if flow["handler"] == "ring"
        )
        == reauth_expected
    )
