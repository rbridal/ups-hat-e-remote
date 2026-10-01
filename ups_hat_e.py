"""I2C reader for the Waveshare UPS HAT (E).

Register map matches rbridal/homeassistant_waveshare_ups_hat_e so the remote
HA integration can reuse the same field names.
"""
from __future__ import annotations

from typing import Any

try:
    import smbus2 as smbus
except ImportError:  # pragma: no cover
    import smbus

DEFAULT_ADDR = 0x2D
DEFAULT_BUS = 1
_NA = 0xFFFF


def _u16(data: list[int], i: int) -> int:
    return data[i] | (data[i + 1] << 8)


def _s16(data: list[int], i: int) -> int:
    val = _u16(data, i)
    if val > 0x7FFF:
        val -= 0x10000
    return val


class UPSHatE:
    """Raw reader for the UPS HAT (E) MCU at 0x2d."""

    def __init__(self, i2c_bus: int = DEFAULT_BUS, addr: int = DEFAULT_ADDR) -> None:
        self.addr = addr
        self.bus = smbus.SMBus(i2c_bus)

    def read(self) -> dict[str, Any]:
        status = self.bus.read_i2c_block_data(self.addr, 0x02, 0x01)[0]
        if status & 0x40:
            state = "fast_charging"
        elif status & 0x80:
            state = "charging"
        elif status & 0x20:
            state = "discharging"
        else:
            state = "idle"

        vbus = self.bus.read_i2c_block_data(self.addr, 0x10, 0x06)
        bat = self.bus.read_i2c_block_data(self.addr, 0x20, 0x0C)
        cells = self.bus.read_i2c_block_data(self.addr, 0x30, 0x08)

        battery_current = _s16(bat, 2)
        time_to_empty = _u16(bat, 8)
        time_to_full = _u16(bat, 10)

        return {
            "status": state,
            "is_charging": state in ("charging", "fast_charging"),
            "is_discharging": state == "discharging",
            "online": state != "discharging",
            "vbus_voltage": _u16(vbus, 0),
            "vbus_current": _u16(vbus, 2),
            "vbus_power": _u16(vbus, 4),
            "battery_voltage": _u16(bat, 0),
            "battery_current": battery_current,
            "battery_percent": _u16(bat, 4),
            "remaining_capacity": _u16(bat, 6),
            "time_to_empty": None
            if (time_to_empty == _NA or battery_current >= 0)
            else time_to_empty,
            "time_to_full": None
            if (time_to_full == _NA or battery_current < 0)
            else time_to_full,
            "cell_voltage_1": _u16(cells, 0),
            "cell_voltage_2": _u16(cells, 2),
            "cell_voltage_3": _u16(cells, 4),
            "cell_voltage_4": _u16(cells, 6),
        }
