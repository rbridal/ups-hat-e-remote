# Waveshare UPS HAT (E) Remote

Reads a Waveshare UPS HAT (E) on a Raspberry Pi (I2C `0x2d`) and publishes the same register payload the local HA integration uses.

Pair with [ha-ups-hat-e-remote](https://github.com/rbridal/ha-ups-hat-e-remote). Point `mqtt.host` at whichever Home Assistant owns this Pi (shop-ha or home-ha Mosquitto).

## Topics

| Topic | Retain | Payload |
|---|---|---|
| `{prefix}/state` | yes | JSON register snapshot |
| `{prefix}/availability` | yes | `online` / `offline` (LWT) |

Default prefix for shop-dash: `ups-hat-e/shop-dash`.

## Install on shop-dash

```bash
curl -fsSL https://raw.githubusercontent.com/rbridal/ups-hat-e-remote/main/scripts/install.sh | bash
```

That clones to `/opt/ups-hat-e-remote`, builds the venv, installs the unit, and stops before start if `config.yaml` still has an empty MQTT password field named `CHANGE_ME`.

Edit `/opt/ups-hat-e-remote/config.yaml` (mode 600). Broker for shop-dash is shop-ha Mosquitto at `172.31.0.20:1883`. A future house Pi uses home-ha at `172.31.0.30:1883`.

Then:

```bash
sudo systemctl enable --now ups-hat-e-remote
```

One-shot read (no MQTT):

```bash
/opt/ups-hat-e-remote/venv/bin/python /opt/ups-hat-e-remote/agent.py --once
```
