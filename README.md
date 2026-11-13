# Bluetooth button hand-off

A small Home Assistant custom integration for event-driven Bluetooth devices (BTHome buttons such as the Shelly BLU
Button, door/window sensors such as the Shelly BLU Door/Window) heard by several Bluetooth proxies.

## The problem

Home Assistant keeps a Bluetooth device on the receiver that delivered its last accepted advertisement. For a device
that only transmits on an event, and so never gets a learned advertising interval, that lasts 15 minutes unless another
receiver hears it about 16 dB louder. Move the button to another room, or mount a sensor where its best proxy can no
longer hear it, and events heard only by other proxies are dropped for up to 15 minutes.
See [home-assistant/core#186689](https://github.com/home-assistant/core/issues/186689).

## What this does

For each address you list, it sets a short fallback availability interval with Home Assistant's public
`bluetooth.async_set_fallback_availability_interval`, at startup and again on every advertisement Home Assistant
accepts from the device (Home Assistant forgets the interval of a quiet device after a few minutes). With an interval of
0.5 s, an event heard only by another proxy is accepted after about 8 s (comparable signal, weak old receiver) or
14 s (any receiver) instead of 15 minutes. Repeated copies of one event are still dropped by bthome-ble's packet id
check, so an event cannot act twice.

It changes nothing else: no scanning mode, no connections, no entities.

## Install

Copy `custom_components/ble_button_handoff` into your Home Assistant `config/custom_components/` folder (or add this
repository to HACS or the Marketplace as a custom repository), then add to `configuration.yaml` or a package:

```yaml
ble_button_handoff:
  interval: 0.5        # seconds, 0.5 to 300, default 2
  addresses:
    - AA:BB:CC:DD:EE:FF   # your device's Bluetooth MAC (Settings > Devices > the BTHome device)
```

Restart Home Assistant. To check it: Settings > Devices & services > Bluetooth > Download diagnostics, and look for
your address under `manager.advertisement_tracker.fallback_intervals` (shown only while the device has been heard in the
last few minutes).

## Tested

Home Assistant 2026.10 and 2026.11 on HAOS, with 14 Shelly Gen2/Gen3 relays as Bluetooth proxies (passive scanning),
two Shelly BLU Button Tough and a Shelly BLU Door/Window (encrypted).

## Remove

Delete the configuration and the folder, restart Home Assistant.

## Licence

MIT, see LICENSE.
