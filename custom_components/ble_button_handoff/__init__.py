"""Bluetooth button hand-off.

Home Assistant's Bluetooth manager keeps a device on the receiver (adapter or proxy) that delivered its last accepted
advertisement. For a device with neither a learned nor a fallback interval that lasts 15 minutes
(FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS in habluetooth), unless another receiver hears it about 16 dB louder.
A BTHome button or door/window sensor only transmits on an event, so once an event reached Home Assistant through
one receiver, a later event that only other receivers hear is dropped for up to 15 minutes.

This integration gives the listed devices a short fallback interval with the public
bluetooth.async_set_fallback_availability_interval. With interval I, habluetooth takes an event from another
receiver once the last accepted one is (I + 5) * 1.5 s old if the signals are comparable and the old receiver is
weak (below -70 dBm), and from any receiver after (I + 5) * 2.5 s: 8.25 and 13.75 s for I = 0.5. Copies of one
event from several receivers arrive within a second or two, well inside that, and bthome-ble drops a repeated
packet id, so one event cannot act twice. Home Assistant removes the interval when a quiet device "disappears"
(every 5 minutes it drops devices silent for longer than their interval + 5 s), so the interval is set again on
every advertisement Home Assistant accepts from the device.

Configuration (configuration.yaml or a package):

    ble_button_handoff:
      interval: 0.5        # seconds, 0.5 to 300, default 2
      addresses:
        - AA:BB:CC:DD:EE:FF

Undo: remove the configuration and this folder, restart Home Assistant.
"""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ble_button_handoff"
CONF_ADDRESSES = "addresses"
CONF_INTERVAL = "interval"

MAC = r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ADDRESSES): vol.All(cv.ensure_list, [cv.matches_regex(MAC)]),
                vol.Optional(CONF_INTERVAL, default=2.0): vol.All(
                    vol.Coerce(float), vol.Range(min=0.5, max=300)
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set the short interval for each listed device, and set it again whenever HA accepts one of its packets."""
    conf = config[DOMAIN]
    interval: float = conf[CONF_INTERVAL]
    addresses = [address.upper() for address in conf[CONF_ADDRESSES]]

    for address in addresses:

        @callback
        def _seen(
            service_info: bluetooth.BluetoothServiceInfoBleak,
            change: bluetooth.BluetoothChange,
            address: str = address,
        ) -> None:
            bluetooth.async_set_fallback_availability_interval(hass, address, interval)

        bluetooth.async_set_fallback_availability_interval(hass, address, interval)
        # PASSIVE: an active mode would register the device for active scans, which puts it on habluetooth's
        # slower "rescue" hand-off path instead of the passive roaming rule this relies on.
        bluetooth.async_register_callback(
            hass,
            _seen,
            bluetooth.BluetoothCallbackMatcher(address=address, connectable=False),
            bluetooth.BluetoothScanningMode.PASSIVE,
        )

    _LOGGER.info(
        "Short receiver hand-off (%s s) for %d Bluetooth devices", interval, len(addresses)
    )
    return True
