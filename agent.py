"""Publish UPS HAT (E) snapshots to an HA Mosquitto broker."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from paho.mqtt.client import CallbackAPIVersion, Client

from ups_hat_e import UPSHatE


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"{path} is not a mapping")
    return data


def _addr(raw) -> int:
    if isinstance(raw, int):
        return raw
    return int(str(raw), 0)


def _payload(cfg: dict, reading: dict) -> str:
    body = {
        "device_id": cfg["device_id"],
        "device_name": cfg.get("device_name") or cfg["device_id"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    body.update(reading)
    return json.dumps(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", nargs="?", default="config.yaml")
    parser.add_argument("--once", action="store_true", help="print one reading and exit")
    args = parser.parse_args()
    cfg = _load(Path(args.config))
    ups = UPSHatE(i2c_bus=int(cfg.get("i2c_bus", 1)), addr=_addr(cfg.get("i2c_addr", "0x2d")))

    if args.once:
        print(_payload(cfg, ups.read()))
        return

    mqtt_cfg = cfg.get("mqtt") or {}
    prefix = str(mqtt_cfg.get("topic_prefix") or f"ups-hat-e/{cfg['device_id']}").rstrip("/")
    state_topic = f"{prefix}/state"
    avail_topic = f"{prefix}/availability"
    interval = int(cfg.get("interval_seconds", 15))

    client = Client(CallbackAPIVersion.VERSION2, client_id=f"ups-hat-e-{cfg['device_id']}")
    username = mqtt_cfg.get("username") or None
    password = mqtt_cfg.get("password") or None
    if password == "CHANGE_ME":
        raise SystemExit("set mqtt.password in config.yaml (or clear it if the broker allows anonymous)")
    if username:
        client.username_pw_set(username, password)
    client.will_set(avail_topic, "offline", qos=1, retain=True)

    def on_connect(c, _userdata, _flags, reason_code, _properties):
        if reason_code == 0:
            c.publish(avail_topic, "online", qos=1, retain=True)

    client.on_connect = on_connect
    client.connect(str(mqtt_cfg.get("host") or "127.0.0.1"), int(mqtt_cfg.get("port") or 1883), keepalive=30)
    client.loop_start()
    try:
        while True:
            try:
                reading = ups.read()
            except OSError as err:
                print(f"i2c read failed: {err}", file=sys.stderr)
                time.sleep(interval)
                continue
            client.publish(state_topic, _payload(cfg, reading), qos=1, retain=True)
            client.publish(avail_topic, "online", qos=1, retain=True)
            time.sleep(interval)
    finally:
        client.publish(avail_topic, "offline", qos=1, retain=True)
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
