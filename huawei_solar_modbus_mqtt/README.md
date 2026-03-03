# huABus - Huawei Solar Modbus via MQTT + Auto-Discovery

Reads data from your Huawei inverter via Modbus TCP and publishes it via MQTT
with automatic Home Assistant discovery.

## About

This app monitors your Huawei solar inverter using Modbus TCP protocol and
publishes all data to MQTT with automatic Home Assistant discovery.
It provides comprehensive monitoring of:

- PV power generation (up to 4 strings)
- Battery status and energy flow
- Grid import/export (3-phase)
- Smart meter data (if available)
- Inverter status and diagnostics

## Features

- **67 Essential Registers** for complete inverter monitoring
- **Automatic Slave ID Detection** — tries common values (1, 2, 100) automatically
- **Total Increasing Filter** — prevents false counter resets in energy statistics,
  active from the very first cycle with no warmup phase
- **3-8s cycle time** for near real-time data
- **Intelligent error tracking** with downtime aggregation and recovery logging
- **MQTT Auto-Discovery** for seamless Home Assistant integration —
  all entities appear automatically under a single device
- **Auto MQTT credentials** — uses Home Assistant MQTT Service by default
- **Comprehensive test suite** — 88% code coverage with unit, integration,
  and end-to-end tests
- **Multi-architecture support** (aarch64, amd64, armhf, armv7, i386)

> ⚠️ **Important:** Huawei inverters allow only **one active Modbus TCP
> connection** at a time. Remove any other Huawei integrations before installing.

For more information, see the [GitHub Repository](https://github.com/arboeh/huABus).
